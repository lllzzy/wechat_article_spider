import time
import json
import re

from selenium import webdriver
from lxml import html


# 获取cookies和token
class Login:
    # 初始化
    def __init__(self):
        self.html = ''

    # 获取cookie
    def get_cookie(self):
        url = 'https://mp.weixin.qq.com'
        Browner = webdriver.Chrome()
        Browner.get(url)

        # 获取账号输入框
        Browner.find_element_by_link_text('使用帐号登录').click()
        ID = Browner.find_element_by_name('account')
        # 获取密码输入框
        PW = Browner.find_element_by_name('password')
        # 输入账号
        id = ''
        pw = ''
        ID.send_keys(id)
        PW.send_keys(pw)
        Browner.find_element_by_class_name('btn_login').click()
        # 等待扫二维码
        time.sleep(20)
        ck = Browner.get_cookies()
        ck1 = json.dumps(ck)
        print(ck1)
        with open('ck.txt', 'w') as f:
            f.write(ck1)
            f.close()
        self.html = Browner.page_source

    # 获取token，在页面中提取
    def get_token(self):
        etree = html.etree
        h = etree.HTML(self.html)
        url = h.xpath('//a[@title="首页"]/@href')[0]
        print(url)
        token = re.findall('\d+', url)[0]
        print(token)
        with open('token.txt', 'w') as f:
            f.write(token)
            f.close()

