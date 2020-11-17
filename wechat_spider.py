# -*- coding: utf-8 -*-

import time
import json

import requests
from lxml import etree
from apscheduler.schedulers.blocking import BlockingScheduler
import pymysql

import mysql_connect
from wechat_login import Login

cookie = ''
token = ''

scheduler = BlockingScheduler()


def get_cookietoken():
    global token, cookie
    with open('token.txt', 'r') as f:
        token = f.read()
        f.close()

    with open('ck.txt', 'r') as f:
        cookie = f.read()
        f.close()

    listCookies = json.loads(cookie)
    cookie = [item["name"] + "=" + item["value"] for item in listCookies]
    cookiestr = '; '.join(item for item in cookie)
    cookie = cookiestr
    print(cookie)
    print(token)


# 从数据库获取公众号的fakeid和name
def get_account():
    sql_getAccount = "select name from wechat_account"
    try:
        account_list = mysql_connect.excute(sql_getAccount)
        return account_list
    except Exception as e:
        print("微信公众号信息获取失败: ", e)


def get_appmsgid(name):
    sql_getAppmsgid = "select appmsgid from article where account='{}' order by appmsgid desc limit 1".format(name)
    try:
        appmsgid = mysql_connect.excute(sql_getAppmsgid)
        print(appmsgid)
        return appmsgid
    except Exception as e:
        print("最新appmsgid获取失败: ", e)


# 解析后的数据插入数据库，使用了ignore进行去重
def insert_db(name, aid, appmsgid, title, date, url, content):
    sql_insert = '''insert into article (account,aid,appmsgid,titile,date,url,content) 
                VALUES('{}', '{}', {}, '{}', '{}','{}', '{}')'''. \
        format(name, aid, appmsgid, title, date, url, pymysql.escape_string(content))
    try:
        print(sql_insert)
        mysql_connect.excute_no_res(sql_insert)
    except Exception as e:
        print('数据插入失败: ', e)


# 通过拿到的文章url获取文章内容
def parse_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
    }
    response = requests.get(url, headers=headers)
    return response.content.decode()


def get_content(html_str):
    html = etree.HTML(html_str)
    content_list = html.xpath("//*[@id=\"js_content\"]//text()")
    # list转字符串
    print(content_list)
    content = '\n'.join(content_list)
    return content


def get_wechatInfo(name):
    global token, cookie
    # 先获取公众号id
    fakeid, acount_name = get_fakeid(name)

    # 查询对应公众号获取到的最新appmsgid
    old_appmsgid = get_appmsgid(acount_name)
    # 目标url
    url = "https://mp.weixin.qq.com/cgi-bin/appmsg"

    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
    }

    # 使用Cookie，跳过登陆操作

    """
    需要提交的data
    fakeid是公众号id
    token需要获取
    """

    data = {
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
        "action": "list_ex",
        "begin": 0,
        "count": "5",
        "query": "",
        "fakeid": fakeid,
        "type": "9",
    }

    # 使用get方法进行提交
    content_json = requests.get(url, headers=headers, params=data).json()
    try:
        for item in content_json["app_msg_list"]:
            # 提取每页文章的标题及对应的url title 日期
            print(item)
            print(old_appmsgid)
            if (len(old_appmsgid) != 0):
                if (int(item["appmsgid"] <= int(old_appmsgid[0]["appmsgid"]))):
                    break
            timeArray = time.localtime(item['create_time'])
            date = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            print(item["title"], date, item["link"])
            url_article = item["link"]
            title = item["title"]
            aid = item["aid"]
            appmsgid = item["appmsgid"]
            html_str = parse_url(url_article)
            content = get_content(html_str)
            insert_db(acount_name, aid, appmsgid, title, date, url_article, content)
            time.sleep(3)
    except Exception as e:
        print("请更新cookie和token", e)
        a = Login()
        a.get_cookie()
        a.get_token()
        scheduler.shutdown()
        scheduler.start()


def get_fakeid(nickname):
    global token, cookie
    try:
        # 返回与输入公众号名称最接近的公众号信息

        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
        }

        search_url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"

        params = {
            "token": token,
            "query": nickname,
            "count": '5',
            "action": "search_biz",
            "ajax": "1",
            "begin": '0',
            "lang": "zh_CN",
            "f": "json",
        }
        session = requests.session()
        content_json = session.get(search_url, headers=headers, params=params)
        fakeid = content_json.json()['list'][0]['fakeid']
        account_name = content_json.json()['list'][0]['nickname']
        return fakeid, account_name

    except Exception as e:
        print("请更新cookie和token", e)
        a = Login()
        a.get_cookie()
        a.get_token()
        scheduler.shutdown()
        scheduler.start()


# 用于定时任务
def job():
    get_cookietoken()
    print('开始执行任务:' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    account_list = get_account()
    for item in account_list:
        get_wechatInfo(item['name'])
        time.sleep(5)


if __name__ == '__main__':
    scheduler.add_job(job, 'cron', day_of_week='0-6', hour='8-22')
    print('任务已开始...........')
    scheduler.start()
