import re
import time
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import os

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
        self.text = ''
        self.status = 0


def timestamp():
    return int(time.time()*1000 )


def get(url, headers={}):
    req = urllib.request.Request(url, None, headers)
    hr = urllib.request.urlopen(req, timeout=2)
    rt = HttpReturn()
    rt.text = hr.read().decode('utf-8')
    rt.status = hr.status
    return rt


def post(url, data=None, headers={}):
    post_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, post_data, headers)
    hr = urllib.request.urlopen(req, timeout=2)
    rt = HttpReturn()
    rt.text = hr.read().decode('utf-8')
    rt.status = hr.status
    return rt


class UserLogin:
    def __init__(self, username, password):
        print('正在登录百度...')
        self.cj = None
        self.isLogin = False
        self.username = username
        self.password = password
        self.token = ''
        if self.__set_cookie():
            return
        self.tt = timestamp()
        if username == '':
            self.username = input('请输入用户名:')
            self.password = input('请输入密码:')
        self.sign_url = 'https://passport.baidu.com/v2/api/?login'
        self.sign_in()

    def __set_cookie(self):
        self.cj = http.cookiejar.LWPCookieJar('Cookie.txt')
        if os.path.exists('Cookie.txt'):
            self.cj.load('Cookie.txt')
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        urllib.request.install_opener(opener)
        urllib.request.urlopen('http://www.baidu.com/')
        return self.__has_sign_in()

    def __get_cookie_str(self):
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
            print("已经登录!")
            self.isLogin = True
            self.cj.save()
            return True

    def __get_token(self, tt):
        """获取token"""
        url = "https://passport.baidu.com/v2/api/?getapi&tpl=pp&apiver=v3&tt=%s&class=login&logintype=dialogLogin" % str(tt)
        rsp = get(url)
        match = re.search('"token" : "(?P<tokenVal>.*?)"', rsp.text)
        token = match.group('tokenVal')
        self.token = token
        return token

    @staticmethod
    def __get_verify_code(code_string):
        """获取验证码"""
        url = "https://passport.baidu.com/cgi-bin/genimage?" + code_string
        rsp = urllib.request.urlopen(url, timeout=2).read()
        path = 'code.jpg'
        with open(path, 'wb') as f:
            f.write(rsp)
            f.flush()
            f.close()
        os.startfile(path)
        time.sleep(0.2)
        code = input("请输入验证码> ")
        return code

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
            'isPhone': 'false'
        }
        return data

    def sign_in(self):
        if self.__has_sign_in():
            print('return')
            return
        self.tt = timestamp()
        token = self.__get_token(timestamp())
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:45.0) Gecko/20100101 Firefox/45.0"
        }
        post_data = self.__first_post()
        header['cookie'] = self.__get_cookie_str()
        rsp = post(self.sign_url, post_data, header)
        match = re.findall('error=(\d+)', rsp.text)
        if not match:
            print(rsp.text)
            return
        if match[0] == '257':
            codestring = re.findall(r'codestring=(.*?)&username', rsp.text)[0]
            code = self.__get_verify_code(codestring)
            post_data = self.__get_post_data(token, codestring, code)
            header['cookie'] = self.__get_cookie_str()
            rsp = post(self.sign_url, post_data, header)
            __match = re.findall('err_no=(\d+)&', rsp.text)
            if not __match:
                print(rsp.text)
            if __match[0] == '0':
                print('登录成功.')
                self.isLogin = True
                self.cj.save()
            else:
                print('登录失败.')
                self.isLogin = False
        elif match[0] == '0':
            print('登录成功.')
            self.isLogin = True
            self.cj.save()
        else:
            print('登录失败.')
        return

if __name__ == '__main__':
    baidu = UserLogin('', '')
    if not baidu.isLogin:
        baidu.sign_in()
