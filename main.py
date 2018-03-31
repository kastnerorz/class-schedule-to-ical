import requests
from icalendar import Calendar, Event
from datetime import datetime
import pytz
import json
import re
from bs4 import BeautifulSoup



url = ['http://xk.shu.edu.cn:8080', 'http://xk.shu.edu.cn']
url_index = url[0]
username = '16122038'
password = 'Dicos.123'
start_date = datetime.datetime(2018,3,25,8,0)

def login(session):
    url_captcha = url_index + '/Login/GetValidateCode?%20%20+%20GetTimestamp()'
    captcha_bin = session.get(url_captcha).content
    captcha_post_data = {'captcha': ('captcha.jpg', captcha_bin, 'image/jpeg')}
    captcha_session = requests.session()
    try:
        captcha_req_result = captcha_session.post('http://114.115.217.207:5000/jwc-xuanke',
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

def _to_time_start(string):
    return datetime.time(8,0) + datetime.timedelta(minutes=45*(int(string) - 1))

def string_to_time(course_time):
    times = []
    text_times = re.findall("[一|二|三|四|五|六|七|八|九|十][0-9]-[0-9]", course_time)

    if re.findall("[0-9]-[0-9]周"):         # 4-10 week

        return times
    elif re.findall("[0-9],[0-9]周"):       # 4,6 week
        return times
    else:                                   # 1-10 week
        for text_time in text_times:
            day = re.findall("[一|二|三|四|五|六|七|八|九|十]", text_time)
            times = re.findall("[0-9]", text_time)
            time_start = int(times[0])
            time_end = int(times[1])
            init_date = start_date + datetime.timedelta(days=day[0], minutes=)

            for i in range(10):
                times.append(start_date + datetime.timedelta(day=))
        return times
class course:
    id = 0
    name = ''
    teacher = ''
    score = 0
    time = ''
    position = ''
    campus = ''

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
    cal.add('prodid', '-//My calendar product//mxm.dk//')
    cal.add('version', '2.0')

    # add events from courses
    for i in range(2, len(course_trs) - 4):
        tds = course_trs[i].find_all('td')

        event = Event()
        event.add('summary', tds[2])    # course name
        event.add('')
if __name__ == '__main__':
    main()