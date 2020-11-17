# -*- coding:utf-8 -*-

import pymysql

database = 'wechat_homework'
#填写用户名密码
conn = pymysql.connect(host='localhost', user='', passwd='', db=database)
cur = conn.cursor(cursor=pymysql.cursors.DictCursor)


def excute_no_res(str):
    reConnect()
    cur.execute(str)
    conn.commit()


def excute(str):
    reConnect()
    cur.execute(str)
    data = cur.fetchall()
    conn.commit()
    return data


# 提交功能
def commit():
    reConnect()
    conn.commit()


# 异常时回滚功能
def rollback():
    conn.rollback()


# 超时重连
def reConnect():
    conn.ping()
