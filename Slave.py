#!/usr/bin/python
# coding=utf-8
# 作者：Shawn
# 邮箱：shawnbluce@gmail.com

from socket import *
import time
import threading
import random
import hashlib
import json


HOST = 'localhost'      # 运行着Controller的机器的IP
PORT = 4022  # 端口
BSIZE = 10240   # 缓冲区大小
ADDRESS = (HOST, PORT)

# 获取一个唯一的ID
TIME_STAMP = str(time.time())   # 时间戳
RANDOM = str(random.uniform(0, 10000))  # 随机数字符串
ENCODING = hashlib.md5((TIME_STAMP + RANDOM).encode('utf-8'))
MY_ID = ENCODING.hexdigest()


# 发送请求
def send_request(input_method, message_list =''):
    global ADDRESS
    global MY_ID
    global BSIZE

    tcp_socket_send = socket(AF_INET, SOCK_STREAM)
    try:
        tcp_socket_send.connect(ADDRESS)
    except Exception:
        print('can\'t connect to server, FAILED!!!')

    # build Json data
    data = '{}'
    data = json.loads(data)
    data["id"] = MY_ID
    data["time"] = str(time.time())
    data["method"] = input_method
    data["url_list"] = str(message_list)

    tcp_socket_send.send(str(data).encode('utf-8'))
    print('send a ' + input_method + ' request')
    response = tcp_socket_send.recv(BSIZE)
    tcp_socket_send.close()
    return response


# 定时6s发送心跳包
def keep_alive():
    while True:
        time.sleep(6)
        send_request('heartbeat')
        print('send a heartbeat package')


# 构建用于提交任务的字符串
def build_submit_list(input_list):
    final = ''
    count = 0
    for i in input_list:
        final = final + '"url' + str(count) + '":"' + i + '",'
        count += 1
    final = '{' + final[0:-1] + '}'
    final = final.strip('"')
    return final


if __name__ == '__main__':
    response = send_request('handshake')
    print('connect to ' + HOST + ':' + str(PORT) + ' ' + response.decode('utf-8'))
    threading.Thread(target=keep_alive).start()
    response = send_request('submit_message', "hello####world####heiheihei####zhanghao")
    response = send_request('get_message')
    print(response)
