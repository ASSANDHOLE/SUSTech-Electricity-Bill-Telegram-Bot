from requests import Session
from re import findall

# you may use this method on other SUSTech CAS services, but might need to change the login url
# example: [BlackBoard](https://bb.sustech.edu.cn) with `https://cas.sustech.edu.cn/cas/login?service=https://bb.sustech.edu.cn/webapps/bb-sso-BBLEARN/index.jsp`
_LOGIN_URL = "https://cas.sustech.edu.cn/cas/login"


def get_sustech_cas_session(username: str, password: str) -> Session:
    s = Session()
    r = s.get(_LOGIN_URL)
    execution = findall('on" value="(.+?)"', r.text)[0]
    data = {
        'username': username,
        'password': password,
        'execution': execution,
        '_eventId': 'submit',
        'geolocation': ''
    }
    r = s.post(_LOGIN_URL, data)
    return s
