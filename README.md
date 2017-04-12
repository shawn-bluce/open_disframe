# 0X00 项目介绍
这是一个采用Python3编写的简单分布式框架。可以通过修改较少的代码将已有程序接入该框架。因为我这里采用的是TCP的SOCKET进行网络通信，所以不是很适合在集群中传递数据量大的数据包。

# 0X01 数据包类型

| 包名 | 中文 | 功能 |
|------|--|--|
| handshake | 握手包 | Slave向Controller发送一个握手包以建立连接 |
| heartbeat | 心跳包 | Slave每隔6秒向Controller发送一个心跳包以确认存活 |
| get_message | 获取消息 | Slave从Controller处获取消息 |
| submit_message | 提交消息 | Slave提交消息到Controller |
| bye | 退出请求 | Slave申请退出集群 |


# 0X02 传递信息的格式
在Slave和Controller之间共享信息是分布式框架的核心功能。现在实现的信息共享功能还很简陋，Slave端如果需要传递两条及以上数据时需要将数据用`####`形式分隔开，比如`hello####world`，然后Slave从Controller获取的数据是`hello\world\`格式的。当然，你也可以自己修改其中的分割方案或者采用二级Json的方案。

# 0X02 接入框架
Controller几乎是不需要进行任何修改的，Slave端也几乎只需要添加自己的代码上去就行。这里举一个例子，比如我想要用这个框架来做一个 **分布式爬虫** 那么应该如何将已经写好的爬虫通过这个框架改为分布式呢？就只需要简单的两步：

#### 1. 确定好在集群中需要传输的数据类型
也就是说你这些爬虫们在集群里需要共享哪些数据。从最简单的来说，单机爬虫会分析页面获取自己需要的数据，也会将页面中的新url放入库中以备接下来的爬取，那就可以将Controller当做库url库用。
#### 2. 如何在集群中传递数据
比如一直爬虫将爬到的新url通过Slave端的`submit_message()`方法将url提交到Controller端；当一只爬虫下载完了需要的数据之后通过`get_message()`方法获取Controller端的数据。

# 0X03 跑起来
部署项目的时候需要注意一点，Controller需要运行在所有Slave都能访问到的位置，比如与Slave在同一内网或者直接放在公网上。
必须要首先运行Controller端，然后再运行Slave端。因为Slave可以动态添加删除，所以只要Controller运行了，以后可以随时添加删除Slave。
