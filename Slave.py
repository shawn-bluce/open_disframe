#!/usr/bin/env python3
# coding=utf-8
# 名称：分布式框架Slave
# 作者：Shawn
# 邮箱：shawnbluce@gmail.com

import time
import random
import hashlib
import socket
import json
import threading

MY_ID = None
BSIZE = 10240
ADDRESS = None


# 获取当前Slave的ID
# ID由第一次调用的时候生成，以后直接获取值
def get_id() -> str:
    global MY_ID

    if MY_ID is None:
        time_stamp = str(time.time())  # 时间戳
        random_number = str(random.uniform(0, 10000))  # 随机数字符串
        string_with_encode = hashlib.md5((time_stamp + random_number).encode('utf-8'))
        MY_ID = string_with_encode.hexdigest()
    return MY_ID


# 设置Master节点的IP和端口号
def setup(host_ip: str, port: int) -> None:
    global ADDRESS
    ADDRESS = (host_ip, port)


# 发送一条请求到Master节点，将响应字符串作为返回值
def send_request(method: str, message_list=None) -> str or None:
    global ADDRESS

    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    json_data = build_request_json(method, message_list)
    try:
        my_socket.connect(ADDRESS)
    except Exception as e:
        print("can't connect to server, FAILED!!!")
        print(e)
        my_socket.close()
        return None
    my_socket.send(json_data.encode('utf-8'))
    response = my_socket.recv(BSIZE)
    my_socket.close()
    now_time = time.ctime().split()
    now_time = now_time[3] + " " + now_time[1] + " " + now_time[2]
    return response.decode('utf-8') + "  time: " + now_time
    # return hashlib.md5(response).hexdigest() + "  time: " + now_time


# 构建与Master通信用的Json数据，将字符串格式的Json数据作为返回值
# message_list是列表
def build_request_json(method: str, message_list: str or None) -> str:
    json_data = {"id": get_id(), "time": str(time.time()), "method": method,
                 "message_list": build_list_json(message_list)}
    json_data = json.dumps(json_data)
    return json_data


# 构建submit_message请求用的消息列表，将列表转成字符串并返回
# message需要是用字符串列表
def build_list_json(message_list: list or None) -> str:
    count = 0
    json_data = {}
    if message_list is None:
        return json.dumps({})
    for message in message_list:
        json_data["message" + str(count)] = message
        count += 1
    return json.dumps(json_data)


# 每6秒发送一波存活证明，以此续命
# 单独开一个线程，死循环执行这个方法
def keep_alive() -> None:
    while True:
        time.sleep(6)
        send_request("heartbeat")
        # print('send heartbeat package to keep alive')


# 测试用，生成随机字符串
def random_str(randomlength=8):
    res = str()
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    for i in range(randomlength):
        res += chars[random.randint(0, length)]
    return res

if __name__ == '__main__':
    setup('localhost', 4022)
    print(send_request("handshake"))
    threading.Thread(target=keep_alive, args=()).start()

    # 测试用，循环提交消息
    # while True:
    #     print(send_request('submit_message', [random_str(7), random_str(7), random_str(7),
    #                                           random_str(7), random_str(7), random_str(7),
    #                                           random_str(7)]))
    #     time.sleep(0.6)

    # 测试用，循环提取消息
    while True:
        print(send_request('get_message'))
        time.sleep(1.8)
