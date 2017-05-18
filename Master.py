#!/usr/bin/env python3
# coding=utf-8
# 名称：分布式框架Master
# 作者：Shawn
# 邮箱：shawnbluce@gmail.com

import multiprocessing
import threading
import socket
import time
import json

SLAVE_LIST = []  # 当前的Slave列表，保存的是Slave实例
SLAVE_LOCK = threading.Lock()  # Slave列表锁
MESSAGE_LIST = multiprocessing.Queue()  # 消息列表
BSIZE = 10240
SERVER_SOCKET = None


class Slave:
    """
    每个Slave实例化成一个对象
    """
    def __init__(self, input_id):
        self.__id = input_id
        self.__hp = 15

    def get_id(self):
        return self.__id

    def is_died(self):
        return self.__hp <= 0

    def hp_less(self, val=1):
        self.__hp -= val

    def hp_add(self):
        self.__hp = 15

    def kill(self):
        self.__hp = 0


def get_server_socket() -> socket.socket:
    """
    获取监听用的Socket，由第一次调用时创建
    :return: Socket
    """
    global SERVER_SOCKET
    if SERVER_SOCKET is None:
        host = ''
        port = 4022
        addr = (host, port)
        SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SERVER_SOCKET.bind(addr)    # 绑定地址和端口
        SERVER_SOCKET.listen(512)  # 最多允许多少连接
        return SERVER_SOCKET
    else:
        return SERVER_SOCKET


def close_connection():
    """
    停止监听，关闭SERVER_SOCKET的连接
    :return: 状态
    """
    global SERVER_SOCKET
    if SERVER_SOCKET is None:
        pass
    else:
        SERVER_SOCKET.close()
    return True


def get_connection() -> socket.socket and dict:
    """
    监听新的连接
    :return: 返回新连接的socket和message
    """
    global BSIZE
    global slave_socket

    server_socket = get_server_socket()
    # print('wait connection')
    slave_socket, slave_addr = server_socket.accept()
    # print('get connection')
    message = slave_socket.recv(BSIZE).decode('utf-8')
    message = json.loads(message)   # 将消息解析成Json
    return slave_socket, message


def process_handshake_request(slave_id: str) -> bool:
    """
    收到了一个handshake包并处理
    :param slave_id: 
    :return: 状态
    """
    global SLAVE_LOCK
    global SLAVE_LIST

    SLAVE_LOCK.acquire()
    SLAVE_LIST.append(Slave(slave_id))  # 加到Slave列表中
    SLAVE_LOCK.release()

    print("get a handshake from: " + slave_id)
    return True


def process_heartbeat_request(slave_id: str) -> bool:
    """
    收到了一个heartbeat包并处理
    :param slave_id: 
    :return: 状态
    """
    global SLAVE_LOCK
    global SLAVE_LIST

    SLAVE_LOCK.acquire()
    # 给Slave恢复生命
    for slave in SLAVE_LIST:
        if slave.get_id() == slave_id:
            slave.hp_add()
            print("get a heartbeat from: " + slave_id)
            break
    SLAVE_LOCK.release()
    return True


def process_submit_message_request(message_json: str) -> bool:
    """
    收到了一个submit_message包并处理
    :param message_json: 消息列表，为json格式的字符串
    :return: 状态
    """
    global MESSAGE_LIST

    recv_message_list = json.loads(message_json)    # 收到提交的消息
    for key in recv_message_list:   # 将消息加到列表中
        MESSAGE_LIST.put(recv_message_list[key])
    return True


def process_get_message_request(slave_id: str, quantity: int) -> str:
    """
    收到了一个get_message包并处理
    :param slave_id: SlaveID
    :param quantity: 要获取的消息数量
    :return: 返回Slave所需的数据
    """
    global MESSAGE_LIST

    message_dict = dict() # 声明返回用的字典
    for i in range(quantity):   # 取出数据放到字典中
        if not MESSAGE_LIST.empty():
            message_dict["message" + str(i)] = MESSAGE_LIST.get(timeout=0.1)
        else:
            if len(message_dict) == 0:
                return json.dumps('null')
    return json.dumps(message_dict) # 将字典转成Json并返回


def process_exit_request(slave_id: str) -> bool:
    """
    收到了一个exit包，并Slave踢出
    :param slave_id: SlaveID
    :return: 状态
    """
    global SLAVE_LOCK
    global SLAVE_LIST

    SLAVE_LOCK.acquire()
    for slave in SLAVE_LIST:    # 杀掉申请退出的Slave
        if slave.get_id() == slave_id:
            slave.kill()
            print("a slave will died: " + slave_id)
            break
    # print('Done')
    SLAVE_LOCK.release()
    return True


def monitor_spider():
    """
    对集群进行实时监控
    每六秒扫视一遍整个集群，将死掉的Slave踢出
    :return: 监控没有返回值
    """
    global SLAVE_LOCK
    global SLAVE_LIST

    while True:
        SLAVE_LOCK.acquire()
        print("There are now " + str(len(SLAVE_LIST)) + " computers")
        SLAVE_LOCK.release()
        time.sleep(6)   # 6秒扫视一遍
        SLAVE_LOCK.acquire()
        while True:
            flag = True     # flag用来标记循环中是否删除了内容，避免数组越界
            for index in range(len(SLAVE_LIST)):
                slave = SLAVE_LIST[index]
                if slave.is_died():
                    print("a slave is died: " + slave.get_id())
                    del SLAVE_LIST[index]   # 删除死掉的Slave
                    flag = False
                    break
                else:
                    slave.hp_less(6)    # 生命值减少6
            if flag:
                break
        SLAVE_LOCK.release()

if __name__ == '__main__':
    get_server_socket()   # 初始化连接
    threading.Thread(target=monitor_spider, args=()).start()   # 开始监控集群

    while True:     # 循环处理连接
        # print("waiting connection...")
        slave_socket, message = get_connection()    # 获取一个连接
        # print("new connection: " + message['id'])
        slave_id = message['id']
        slave_method = message['method']

        # 将连接分类处理
        if slave_method == 'handshake':
            # print("have a new slave")
            process_handshake_request(slave_id)
            slave_socket.send("handshake success".encode('utf-8'))
            continue
        elif slave_method == 'heartbeat':
            # print("have a new heartbeat")
            process_heartbeat_request(slave_id)
            slave_socket.send("heartbeat success".encode('utf-8'))
            continue
        elif slave_method == 'submit_message':
            # print("have a new submit")
            process_submit_message_request(message['message_list'])
            slave_socket.send("submit success".encode('utf-8'))
            continue
        elif slave_method == 'get_message':
            # print("have a new get")
            send_message_list = process_get_message_request(slave_id, 10)
            slave_socket.send(send_message_list.encode('utf-8'))
            continue
        elif slave_method == 'exit':
            # print("have a new exit")
            process_exit_request(slave_id)
            slave_socket.send("exit success".encode('utf-8'))
            continue
        else:
            # print("have a Error request!!!")
            slave_socket.send(("not found request: " + slave_method).encode('utf-8'))
