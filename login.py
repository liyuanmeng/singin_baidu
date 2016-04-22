import re
import time
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import os
import hashlib


#  err_no   0:登录成功，４:密码错误，６:验证码错误, 527:请输入验证码　　　

L_HEADER = {
    "Host": "passport.baidu.com",
    "Referer": "http://www.baidu.com/cache/user/html/login-1.2.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:45.0) Gecko/20100101 Firefox/45.0",
    "Origin": "http://www.baidu.com",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive"
}

R_HEADER = {
    "Host": "zhidao.baidu.com",
    "User-Agent": 'Mozilla/5.0 (Windows NT 6.1; rv:45.0) Gecko/20100101 Firefox/45.0',
    "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    "Referer": "http://zhidao.baidu.com/uadmin/commontag",
    "Connection": "keep - alive",
    "Cache - Control": "max - age = 0"
}


class HttpReturn:
    def __init__(self):
        self.text = 'timeout'
        self.status = 0
        self.obj = None


def timestamp():
    return int(time.time()*1000)


def now():
    nt = time.localtime()
    return '%d-%02d-%02d %02d:%02d:%02d# ' % (nt.tm_year, nt.tm_mon, nt.tm_mday, nt.tm_hour, nt.tm_min, nt.tm_sec)


def get(url, headers=None, timeout=2, decode='utf-8'):
    rt = HttpReturn()
    try:
        if headers is None:
            hr = urllib.request.urlopen(url, timeout=timeout)
        else:
            req = urllib.request.Request(url, None, headers)
            hr = urllib.request.urlopen(req, timeout=timeout)
        rt.obj = hr
        rt.text = hr.read().decode(decode)
        rt.status = hr.status
    finally:
        return rt


def post(url, data=None, headers=None, timeout=2, decode='utf-8'):
    rt = HttpReturn()
    if headers is None:
        headers = {}
    post_data = urllib.parse.urlencode(data).encode(decode)
    try:
        req = urllib.request.Request(url, post_data, headers)
        hr = urllib.request.urlopen(req, timeout=timeout)
        rt = HttpReturn()
        rt.obj = rt
        rt.text = hr.read().decode('utf-8')
        rt.status = hr.status
    finally:
        return rt


def down(url, path, headers=None):
    try:
        if headers is None:
            hr = urllib.request.urlopen(url)
        else:
            req = urllib.request.Request(url, None, headers)
            hr = urllib.request.urlopen(req)
        with open(path, 'wb') as f:
            f.write(hr.read())
            f.flush()
            f.close()
    except Exception as e:
        print(e)
        return False
    return True


def get_md5(username):
    return hashlib.md5(username.encode()).hexdigest()


class UserLogin:
    __header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:45.0) Gecko/20100101 Firefox/45.0"
        }

    def __init__(self, username, password, mem_pass=True):
        print(now(), '正在登录百度...')
        self.mem_pass = mem_pass
        self.cj = None
        self.isLogin = False
        self.token = ''
        self.Cookies = {}
        self.now_user = ''
        if username == '' and password == '':
            self.username = input('请输入用户名:')
            self.password = input('请输入密码:')
        else:
            self.username = username
            self.password = password
        if self.__set_cookie():
            if self.now_user == self.username:
                return
        self.tt = timestamp()
        self.sign_url = 'https://passport.baidu.com/v2/api/?login'
        self.sign_in()

    def __set_cookie(self):
        fn = get_md5(self.username) + '.txt'
        self.cj = http.cookiejar.MozillaCookieJar(fn)   # LWPCookieJar('Cookie.txt')
        if self.mem_pass:
            if os.path.exists(fn):
                self.cj.load(fn)
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        urllib.request.install_opener(opener)
        urllib.request.urlopen('http://www.baidu.com/')
        return self.__has_sign_in()

    def get_cookie_str(self):
        rt = ''
        for item in self.cj:
            t = re.search('\S+=\S+', str(item)).group(0)
            k = t[:t.index('=')]
            v = t[len(k) + 1:]
            rt += k+'='+v+';'
        return rt[:-1]

    def __has_sign_in(self):
        """ 检查是否已经登录 """
        rsp = get('http://www.baidu.com')
        if '登录' in rsp.text:
            self.isLogin = False
            return False
        else:
            m = re.findall('<span class=user-name>([^>]+)</span>', rsp.text)
            self.now_user = m[0]
            print("用户%s已经登录!" % self.now_user)
            self.isLogin = True
            self.cj.save()
            for item in self.cj:
                t = re.search('\S+=\S+', str(item)).group(0)
                k = t[:t.index('=')]
                v = t[len(k) + 1:]
                self.Cookies[k] = v
            return True

    def __get_token(self, tt):
        """获取token"""
        url = "https://passport.baidu.com/v2/api/?getapi&tpl=pp&apiver=v3&tt=%s&class=login&logintype=dialogLogin" \
              % str(tt)
        self.__header['cookit'] = self.get_cookie_str()
        rsp = get(url, self.__header)
        match = re.search('"token" : "(?P<tokenVal>.*?)"', rsp.text)
        token = match.group('tokenVal')
        self.token = token
        return token

    @staticmethod
    def __get_verify_code(code_string):
        """获取验证码"""
        url = "https://passport.baidu.com/cgi-bin/genimage?" + code_string
        path = 'code.jpg'
        if down(url, path):
            os.startfile(path)
            time.sleep(0.2)
            code = input("请输入验证码> ")
            return code
        else:
            print('不能下载验证码!')
            return ''

    def __get_post_data(self, token, codestring, verify_code):
        post_data = {
            'apiver': 'v3',
            'codestring': codestring,
            'isPhone': '',
            'logLoginType': ' pc_loginDialog',
            'loginmerge': 'true',
            'logintype': 'dialogLogin',
            'mem_pass': 'on',
            'password': self.password,
            'ppui_logintime': '5452',
            'quick_user': '0',
            'safeflg': '0',
            'splogin': 'newuser',
            'staticpage': 'https://www.baidu.com/cache/user/html/v3Jump.html',
            'token': token,
            'tpl': 'mn',
            'tt': str(timestamp()),
            'u': 'https://www.baidu.com/',
            'username': self.username,
            'verifycode': verify_code,
        }
        return post_data

    def __first_post(self):
        data = {
            'username': self.username,
            'password': self.password,
            'u': 'https://passport.baidu.com/',
            'tpl': 'pp',
            'token': self.token,
            'codestring': '',
            'verifycode': '',
            'staticpage': 'https://passport.baidu.com/static/passpc-account/html/v3Jump.html',
            'isPhone': 'false',
            'mem_pass': 'on'
        }
        return data

    def sign_in(self):
        if self.__has_sign_in():
            print(now(), '已登录.')
            return
        self.tt = timestamp()
        token = self.__get_token(timestamp())
        post_data = self.__first_post()
        self.__header['cookit'] = self.get_cookie_str()
        rsp = post(self.sign_url, post_data, self.__header)
        match = re.findall('error=(\d+)', rsp.text)
        if not match:
            print(rsp.text)
            return
        if match[0] == '257':
            codestring = re.findall(r'codestring=(.*?)&username', rsp.text)[0]
            code = self.__get_verify_code(codestring)
            post_data = self.__get_post_data(token, codestring, code)
            self.__header['cookit'] = self.get_cookie_str()
            rsp = post(self.sign_url, post_data, self.__header)
            __match = re.findall('err_no=(\d+)&', rsp.text)
            if not __match:
                print(rsp.text)
            if __match[0] == '0':
                # print(now(), '登录成功.')
                # self.isLogin = True
                # self.cj.save()
                pass
            else:
                print(now(), '登录失败. 错误代码:', __match[0])
                self.isLogin = False
        elif match[0] == '0':
            # print(now(), '登录成功.')
            # self.isLogin = True
            # self.cj.save()
            pass
        else:
            print(now(), '登录失败. 错误代码:', match[0])
        return self.__has_sign_in()
'''
if __name__ == '__main__':
    baidu = UserLogin('', '')
    if not baidu.isLogin:
        baidu.sign_in()
'''
