# 0X00 项目介绍
这是一个采用Python3编写的简单分布式框架。可以通过修改较少的代码将已有程序接入该框架。因为我这里采用的是TCP的SOCKET进行网络通信，所以不是很适合在集群中传递数据量大的数据包。

# 0X01 应用到的技术
* 单个节点采用了多线程和同步锁
* 使用列表和锁实现了简单的消息队列
* 实现了简单的心跳检测

# 0X02 数据包类型

| 包名 | 中文 | 功能 |
|------|--|--|
| handshake | 握手包 | Slave向Master发送一个握手包以建立连接 |
| heartbeat | 心跳包 | Slave每隔6秒向Master发送一个心跳包以确认存活 |
| get_message | 获取消息 | Slave从Master处获取消息 |
| submit_message | 提交消息 | Slave提交消息到Master |
| exit | 退出请求 | Slave申请退出集群 |


# 0X03 传递信息的格式
在Slave和Master之间共享信息是分布式框架的核心功能。数据传输采用Json格式，格式如下
```json
{
    "id":"aa519a9964e90c1f3d5145c0a03015c5",
    "time":"1494649076.5362635",
    "method":"submit_message",
    "message_list":"{"message0": "EY0RMze", "message1": "9NJi4S0", "message2": "fT4pU9i", "message3": "ZMF9YCR", "message4": "xAxgxjN", "message5": "NLtMzRw", "message6": "yRq5bg6"}"
}
```
这里的`message_list`是携带的数据，携带的数据也是Json格式的。

# 0X04 接入框架
Master几乎是不需要进行任何修改的，Slave端也几乎只需要添加自己的代码上去并修改IP就行。这里举一个例子，比如我想要用这个框架来做一个 **分布式爬虫** 那么应该如何将已经写好的爬虫通过这个框架改为分布式呢？就只需要简单的两步：

#### 1. 确定好在集群中需要传输的数据类型
也就是说你这些爬虫们在集群里需要共享哪些数据。从最简单的来说，单机爬虫会分析页面获取自己需要的数据，也会将页面中的新url放入库中以备接下来的爬取，那就可以将Master当做库url库用。
#### 2. 如何在集群中传递数据
比如一直爬虫将爬到的新url通过Slave端的`submit_message()`方法将url提交到Controller端；当一只爬虫下载完了需要的数据之后通过`get_message()`方法获取Master端的数据。

# 0X03 跑起来
部署项目的时候需要注意一点，Master需要运行在所有Slave都能访问到的位置，比如与Slave在同一内网或者直接放在公网上。
必须要首先运行Master端，然后再运行Slave端。因为Slave可以动态添加删除，所以只要Master运行了，以后可以随时添加删除Slave。
