import requests
from icalendar import Calendar, Event, vText
import datetime
import pytz
import json
import re
from bs4 import BeautifulSoup
import tempfile, os

url = ['http://xk.shu.edu.cn:8080', 'http://xk.shu.edu.cn']
url_index = url[0]
username = ''
password = ''
year = 2018
month = 9
day = 2
term_start_date = datetime.datetime(year, month, day, 8, 0, tzinfo=pytz.timezone('Asia/Shanghai'))


def login(session):
    url_captcha = url_index + '/Login/GetValidateCode?%20%20+%20GetTimestamp()'
    captcha_bin = session.get(url_captcha).content
    captcha_post_data = {'captcha': ('captcha.jpg', captcha_bin, 'image/jpeg')}
    captcha_session = requests.session()
    try:
        captcha_req_result = captcha_session.post('http://shuhelper.cn:8001/jwc',
                                                  files=captcha_post_data,
                                                  timeout=10)
        captcha_text = captcha_req_result.json()['result']
    except:
        print(u'获取验证码失败')
        captcha_session.keep_alive = False
        print(u'close captcha session...')
        return False
    login_data = {
        'txtUserName': username,
        'txtPassword': password,
        'txtValiCode': captcha_text
    }
    print(u'正在登录...')
    ReqLogin = session.post(url_index, login_data)
    Result = re.findall(u'divLoginAlert">\r\n\s*(.*?)\r\n', ReqLogin.text)
    if not Result:
        # try:
        #     Semester = re.findall(u'<font color="red">(.*?)<', ReqLogin.content)[0]
        #     LoginInfo = re.findall(u'23px;">\r\n\s*(.*?)：(.*?)\r\n', ReqLogin.text)
        # except:
        #     print(u'[get semester info error]')
        #     return False
        # print('%s' % Semester)
        # for info in LoginInfo:
        #     print('%s:%s' % info)
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
    headers = {'user-agent',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
               'AppleWebKit/537.36 (KHTML, like Gecko)'
               'Chrome/63.0.3239.132 Safari/537.36'
               }

    req = requests.Session()
    while not login(req):
        print(u'login failed')
    course_req_post_data = {'studentNo': username}
    course_req_result = req.post(url_index + '/StudentQuery/CtrlViewQueryCourseTable', course_req_post_data)
    print(course_req_result.text)
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


if __name__ == '__main__':
    main()
