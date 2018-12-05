import datetime
import re

import pytz
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vText

# config
url = ['http://xk.autoisp.shu.edu.cn:8080', 'http://xk.autoisp.shu.edu.cn']
url_index = url[1]  # i = 0 or 1
username = 'YOUR_ID'
password = 'YOUR_PASSWORD'
year = 2018, month = 11, day = 26  # term start date (Monday)

term_start_date = datetime.datetime(year, month, day - 1, 8, 0, tzinfo=pytz.timezone('Asia/Shanghai'))


def login(session):
    # authorize
    authorize_r = requests.get(
        'https://oauth.shu.edu.cn/oauth/authorize?response_type=code&client_id=yRQLJfUsx326fSeKNUCtooKw&redirect_uri=http%3a%2f%2fxk.autoisp.shu.edu.cn%2fpassport%2freturn')
    soup = BeautifulSoup(authorize_r.text, "html.parser")
    saml_request = soup.find_all(attrs={'name': 'SAMLRequest'})[0]['value']
    relay_state = soup.find_all(attrs={'name': 'RelayState'})[0]['value']

    # SSO
    sso_data = {
        'SAMLRequest': saml_request,
        'RelayState': relay_state
    }
    session.post('https://sso.shu.edu.cn/idp/profile/SAML2/POST/SSO',
                 data=sso_data)

    # UserPassword
    user_password_data = {
        'j_username': username,
        'j_password': password
    }
    user_password_r = session.post('https://sso.shu.edu.cn/idp/Authn/UserPassword',
                                   cookies=session.cookies,
                                   data=user_password_data)
    soup = BeautifulSoup(user_password_r.text, 'html.parser')
    relay_state = soup.find_all(attrs={'name': 'RelayState'})[0]['value']
    saml_response = soup.find_all(attrs={'name': 'SAMLResponse'})[0]['value']

    # POST
    post_data = {
        'RelayState': relay_state,
        'SAMLResponse': saml_response
    }
    post_r = session.post('http://oauth.shu.edu.cn/oauth/Shibboleth.sso/SAML2/POST',
                          data=post_data)
    Result = re.findall(u'divLoginAlert">\r\n\s*(.*?)\r\n', post_r.text)
    if not Result:
        print(u'登录成功!')
        return True
    else:
        print(u'[登录失败]', Result[0])
        return False


def display(cal):
    return cal.to_ical().replace('\r\n', '\n').strip()


def string_to_int(num):
    if num == '一':
        return 1
    elif num == '二':
        return 2
    elif num == '三':
        return 3
    elif num == '四':
        return 4
    elif num == '五':
        return 5


def string_to_time(course_time):  # '二1-2 三3-4'
    """

    :param course_time: '二1-2'
    :return: 十周或若干周的上课下课时间 [{start_time, end_time},...]

    """
    course_times = []
    course_minutes = [0, 55, 120, 175, 250, 295, 370, 425, 480, 535, 600, 655, 710]
    available_weeks = range(1, 11)
    text_times = re.findall("[一|二|三|四|五|六|七|八|九|十]\d?\d-\d?\d", course_time)  # ['二1-2', '三3-4']

    # part of weeks like: 4 - 6
    if re.findall("\d-\d?\d周", course_time):

        part_week = re.findall("\d-\d?\d周", course_time)
        weeks = re.findall("\d\d*", part_week[0])
        start_week = int(weeks[0])
        end_week = int(weeks[1])
        available_weeks = range(start_week, end_week + 1)

    # some of weeks like: 1, 6
    elif re.findall("\d,\d?\d周", course_time):

        part_week = re.findall("\d,\d?\d周", course_time)
        week1 = re.findall("\d", part_week[0])[0]
        week2 = re.findall("\d?\d", part_week[0])[1]
        available_weeks = [int(week1), int(week2)]

    # full ten weeks
    for text_time in text_times:
        day = re.findall("[一|二|三|四|五|六|七|八|九|十]", text_time)
        times = re.findall("\d\d*", text_time)
        time_start = int(times[0])
        time_end = int(times[1])
        for i in available_weeks:
            course_times.append({
                'start_time': term_start_date + datetime.timedelta(days=string_to_int(day[0]),
                                                                   weeks=i - 1,
                                                                   minutes=course_minutes[time_start - 1]),
                'end_time': term_start_date + datetime.timedelta(days=string_to_int(day[0]) + (i - 1) * 7,
                                                                 minutes=course_minutes[time_end - 1] + 45)
            })
    return course_times


def main():
    # login
    req = requests.Session()
    while not login(req):
        print(u'login failed')

    print('正在处理...')
    course_req_post_data = {'studentNo': username}
    course_req_result = req.post(url_index + '/StudentQuery/CtrlViewQueryCourseTable', course_req_post_data)
    soup = BeautifulSoup(course_req_result.text, "html.parser")

    course_table = soup.table
    course_trs = course_table.find_all('tr')

    # init calendar
    cal = Calendar()
    cal.add('prodid', 'class')
    cal.add('version', '2.0')

    # add events from courses
    for i in range(3, len(course_trs) - 1):
        tds = course_trs[i].find_all('td')
        course_times = string_to_time(tds[6].text)
        for index, time in enumerate(course_times):
            event = Event()
            event.add('summary', tds[2].text.replace("\n", "").strip())  # course name
            event.add('dtstart', time['start_time'])  # course start time
            event.add('dtend', time['end_time'])  # course end time
            event.add('dtstamp', datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai')))  # course edit time
            event['location'] = vText(tds[7].text.replace("\n", "").strip())  # course location
            event['uid'] = vText(tds[1].text.replace("\n", "").strip() +
                                 tds[3].text.replace("\n", "").strip() +
                                 str(index))  # course id + teacher id
            cal.add_component(event)

    # write to ics
    with open('class_schedule.ics', 'wb') as f:
        f.write(cal.to_ical())
    print('输出成功！请将 `class_schedule.ics` 文件导入到日历。')

if __name__ == '__main__':
    main()
