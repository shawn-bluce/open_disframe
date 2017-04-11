#!/usr/bin/env python3
# coding=utf-8
# 作者：Shawn
# 邮箱：shawnbluce@gmail.com

from __future__ import print_function
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
import time
import json


LIVING_HOST = []  # 保存当前存活的Slave
MESSAGE_LIST = []  # 等待分配的任务列表
LOCK_LIVING_HOST = Lock()   # Slave列表锁
LOCK_MESSAGE_LIST = Lock()     # Message列表锁
HOST = ''
PORT = 4022  # 使用端口
BSIZE = 10240  # 缓冲区大小
ADDRESS = (HOST, PORT)

# 配置socket，绑定地址，最大连接数为100
TCP_SOCKET = socket(AF_INET, SOCK_STREAM)
TCP_SOCKET.bind(ADDRESS)
TCP_SOCKET.listen(100)


# Slave节点类
class Slave:
    def __init__(self, input_id):
        self.__id = input_id    # 设置一个ID
        self.__hp = 15          # 生命值，默认设置为15

    def get_id(self):
        return self.__id

    def is_died(self):
        return self.__hp <= 0

    def hp_less(self):
        self.__hp -= 1

    def hp_restore(self):
        self.__hp = 15

    def kill(self):
        self.__hp = 0


# 等待并获得一个连接，将连接的socket和数据返回
def listen_slave():
    global TCP_SOCKET
    global BSIZE

    print('waiting connection')
    tcp_socket_slave, slave_address = TCP_SOCKET.accept()  # 连接
    print('new connection')
    receive_data = tcp_socket_slave.recv(BSIZE)  # 接收数据
    return tcp_socket_slave, receive_data  # 返回socket和数据


# 收到了一个握手包
def handshake_package(input_slave_id):
    global LOCK_LIVING_HOST
    global LIVING_HOST

    # 实例化一个Slave并将其加入列表中
    LOCK_LIVING_HOST.acquire()
    new_slave = Slave(input_slave_id)
    LIVING_HOST.append(new_slave)
    LOCK_LIVING_HOST.release()

    print('get a connect from: ' + str(input_slave_id))


# 收到了一个心跳包
def heartbeat_package(input_slave_id):
    global LOCK_LIVING_HOST
    global LIVING_HOST

    # 将发送心跳包的Slave生命值恢复至满
    LOCK_LIVING_HOST.acquire()
    for slave in LIVING_HOST:
        if slave.get_id() == input_slave_id:
            slave.hp_restore()
            break
    LOCK_LIVING_HOST.release()
    print(str(input_slave_id) + ' is living')


# 向Slave发送消息
def get_message(input_number):
    global LOCK_MESSAGE_LIST
    global MESSAGE_LIST

    LOCK_MESSAGE_LIST.acquire()
    sub_message_list = MESSAGE_LIST[:input_number]
    del MESSAGE_LIST[:input_number]
    LOCK_MESSAGE_LIST.release()
    result = ''
    for message in sub_message_list:
        result = result + message + '\\'
    return result


# 接收Slave的添加请求
def add_message(input_new_message):
    global LOCK_MESSAGE_LIST
    global MESSAGE_LIST

    LOCK_MESSAGE_LIST.acquire()
    print(input_new_message)
    MESSAGE_LIST.extend(input_new_message)
    LOCK_MESSAGE_LIST.release()


# Slave主动申请退出系统
def slave_exit(input_slave_id):
    global LOCK_LIVING_HOST
    global LIVING_HOST

    LOCK_LIVING_HOST.acquire()
    for slave in LIVING_HOST:
        if slave.get_id() == input_slave_id:
            slave.kill()
            print(slave.get_id(), ' will died')
            break
    LOCK_LIVING_HOST.release()


# 实时监控Slave，负责每秒钟掉血并踢出Slave
def monitor_slave():
    global LIVING_HOST
    global LOCK_LIVING_HOST

    while True:
        LOCK_LIVING_HOST.acquire()
        print('The number of current slaves is ', len(LIVING_HOST))
        LOCK_LIVING_HOST.release()
        time.sleep(3)   # 每隔三秒钟检查一次
        index = 0
        for slave in LIVING_HOST:
            if slave.is_died():  # 将死亡的踢出
                LOCK_LIVING_HOST.acquire()
                print(LIVING_HOST[index].get_id(), ' is died')
                del LIVING_HOST[index]
                LOCK_LIVING_HOST.release()
                break
            else:   # 活着的减血
                slave.hp_less()
            index += 1


if __name__ == '__main__':

    # 开始监控
    Thread(target=monitor_slave).start()
    while True:
        socket, data = listen_slave()
        data = data.decode('utf-8')
        data = data.replace('\\"', '"')
        a = data[:data.index('url_list')]
        b = data[data.index('url_list'):]
        if len(b) > 14:
            b = 'url_list": ' + b[11:-1].strip('"') + '}'
        data = a + b
        data = data.replace('\'', '"')
        print(data)
        try:
            data = json.loads(data)
            print('message len is ', len(MESSAGE_LIST))
        except ValueError:
            socket.close()
            break
        method = data['method']
        input_slave_id = data['id']

        # 处理握手包
        if method == 'handshake':
            handshake_package(input_slave_id)
            socket.send('OK'.encode('utf-8'))
            print('new host , now living host:', len(LIVING_HOST))

        # 处理心跳包
        elif method == 'heartbeat':
            heartbeat_package(input_slave_id)
            print(input_slave_id, '   heartbeat hp add to 15')
            socket.send('OK'.encode('utf-8'))

        # 处理get_message包
        elif method == 'get_message':
            print('getting message')
            slave_message = get_message(5)
            print('wile send message')
            print(slave_message)
            socket.send(slave_message.encode('utf-8'))
            print('send message done')

        # 处理退出请求
        elif method == 'bye':
            slave_exit(input_slave_id)
            socket.send('OK'.encode('utf-8'))
            print('Living host :', len(LIVING_HOST))

        # 处理submit_message包
        elif method == 'submit_message':
            new_message = data['url_list']
            new_message = new_message.split('####')  # 默认采用四个#分割
            message_list = []
            for message in new_message:
                message_list.append(message)
            add_message(message_list)
            socket.send('OK'.encode('utf-8'))
            print('new message')

        else:
            socket.send('404 method Not Found')