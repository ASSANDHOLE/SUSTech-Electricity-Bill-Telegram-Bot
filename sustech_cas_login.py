from requests import Session
from re import findall

_LOGIN_URL = "https://cas.sustech.edu.cn/cas/login"


def connect(username: str, password: str) -> Session:
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
