import json

import redis
import threading
from django.conf import settings


# 自定义redis通信线路协议
# 请求 request = {'sync': str, 'timeout': float, 'body': str/dict} sync同步响应通道, timeout响应超时时间, body请求体
# 应答 response = {'ok': bool, 'body': str/dict} ok请求是否成功, body响应体
# 汇报 report = {'body': str/dict} body汇报体

# class Group

class PubSub:
    def __init__(self):
        self.pool = redis.ConnectionPool(host=settings.REDIS['HOST'], port=settings.REDIS['PORT'],
                                         db=settings.REDIS['DB'], password=settings.REDIS['PASSWORD'])
        self.client = redis.StrictRedis(connection_pool=self.pool)
        self.pubsub = self.client.pubsub()
        # print("+++++++++++++++++++++++", self.pool)
        # print("+++++++++++++++++++++++", self.client)
        # print("+++++++++++++++++++++++", self.pubsub)

        self.pubsub.ping()  # 创建连接
        self.pubsub_thread = None

        self.sync_cv = threading.Condition()
        self.sync_msg = ""

        self.pubsub_array = dict()  # 存放新建的私有pubsub以及工作线程[pubsub, thread]

    # 获取通道的订阅者个数
    def numsub(self, channel):
        res = self.client.pubsub_numsub(channel)
        return res[0][1]

    # 添加订阅的通道
    def subscribe(self, channel, callback, private_ps=None):
        if private_ps:
            # print("subscribe private_ps: %s" % private_ps)
            if private_ps in self.pubsub_array:  # 已存在则取出
                pubsub = self.pubsub_array[private_ps][0]
                pubsub.subscribe(**{channel: callback})
            else:  # 不存在则创建
                pubsub = self.client.pubsub()
                pubsub.subscribe(**{channel: callback})
                t = pubsub.run_in_thread(10.0)  # 启动监听线程
                self.pubsub_array[private_ps] = [pubsub, t]
            return

        self.pubsub.subscribe(**{channel: callback})
        if self.pubsub_thread is None:
            self.pubsub_thread = self.pubsub.run_in_thread(1.0, daemon=True)

    # @brief 取消订阅
    # @param channel 取消订阅的通道
    # @param private_ps 所在的私有pubsub(默认为None, self.pubsub)
    # @param _all 是否取消所有订阅
    def unsubscribe(self, channel, private_ps=None, _all=False):
        if private_ps:
            if private_ps not in self.pubsub_array:
                return

            pubsub, t = self.pubsub_array[private_ps]
            if _all:
                t.stop()  # 停止工作线程
                t.join()  # 等待线程退出
                pubsub.close()
            else:
                pubsub.unsubscribe(channel)

            # 由于subscribed函数被property装饰,因此访问时不能加()
            if not pubsub.subscribed:  # 无监听通道, 删除监听器pubsub
                t.stop()  # 停止工作线程
                t.join()  # 等待线程退出
                print(self.pubsub_array)
                self.pubsub_array.pop(private_ps)
        else:
            if _all:
                self.pubsub_thread.stop()
                self.pubsub_thread.join()
                self.pubsub.close()
            else:
                self.pubsub.unsubscribe(channel)
                if not self.pubsub.subscribed:
                    self.pubsub_thread.stop()  # 停止工作线程
                    self.pubsub_thread.join()  # 等待线程退出

    # 订阅一个或多个给定模式的通道
    # @param private_ps 私有ps名称, 当非None时创建新的self.client.pubsub()
    #                   私有ps用于解决同一数据的分发问题, 若多次向同一通道绑定不同的回调函数, 只有最后一个生效, 导致之前的无法接受数据
    #                   使用多个私有ps订阅相同的通道则解决了此问题(依靠Redis.PubSub的多线程)
    def psubscribe(self, channel, callback, private_ps=None):
        if private_ps:
            # print("psubscribe private_ps: %s" % private_ps)
            if private_ps in self.pubsub_array:  # 已存在则取出
                pubsub = self.pubsub_array[private_ps][0]
                pubsub.psubscribe(**{channel: callback})
            else:  # 不存在则创建
                pubsub = self.client.pubsub()
                pubsub.psubscribe(**{channel: callback})
                t = pubsub.run_in_thread(10.0)  # 启动监听线程
                self.pubsub_array[private_ps] = [pubsub, t]
            return

        self.pubsub.psubscribe(**{channel: callback})
        if self.pubsub_thread is None:
            self.pubsub_thread = self.pubsub.run_in_thread(1.0, daemon=True)

    def punsubscribe(self, channel, private_ps=None):
        # print("%s in self.pubsub_array?" % private_ps, private_ps in self.pubsub_array)
        if private_ps:
            if private_ps not in self.pubsub_array:
                return

            pubsub, t = self.pubsub_array[private_ps]
            pubsub.punsubscribe(channel)

            # 由于subscribed函数被property装饰,因此访问时不能加()
            if not pubsub.subscribed:  # 无监听通道, 删除监听器pubsub
                t.stop()  # 关闭监听线程
                t.join()
                self.pubsub_array.pop(private_ps)  # 从库中删除
            return

        self.pubsub.punsubscribe(channel)
        if not self.pubsub.subscribed:
            self.pubsub_thread.stop()  # 停止工作线程
            self.pubsub_thread.join()  # 等待线程退出

    # channel 发布通道
    # msg 发布消息 str/dict
    def publish(self, channel, msg, publisher=None):
        request = {'body': msg}
        if publisher:
            request['pub'] = publisher

        self.client.publish(channel, json.dumps(request))

    # 接收同步通道的信息
    def _onSyncMessage(self, item: dict):
        self.sync_cv.acquire()
        self.sync_msg = item['data']
        print("_onSyncMessage", self.sync_msg)
        self.sync_cv.notify()
        self.pubsub.unsubscribe(item['channel'])  # 不再订阅
        self.sync_cv.release()

    # 同步请求
    # @param channel 发布请求的通道
    # @param msg 请求消息
    # @param sync_channel 同步响应的通道
    # @param timeout 响应超时时间 float(s)
    def sync_request(self, channel, msg, sync_channel, timeout=0):
        print("sync_request-> channel: %s, sync_channel: %s" % (channel, sync_channel))
        if self.numsub(channel) < 1:
            return False, "offline"

        request = {'sync': sync_channel, 'timeout': timeout, 'body': msg}

        self.sync_cv.acquire()
        self.subscribe(sync_channel, self._onSyncMessage)
        self.client.publish(channel, json.dumps(request))
        if self.sync_cv.wait(timeout):
            self.sync_cv.release()
            return True, self.sync_msg

        self.sync_cv.release()
        return False, "timeout"

    # 同步响应
    # @param channel 响应请求的通道
    # @param response 应答消息
    # @param ok 应答是否成功
    # @param error_msg 错误信息
    def sync_response(self, channel, response, error_msg=None):
        response = {'ok': error_msg is None, 'body': response}
        if error_msg:
            response['error_msg'] = error_msg
        self.client.publish(channel, json.dumps(response))


def carCmdChannelPrefix(groupid: str):
    return str(groupid) + "_car_cmd"


# 车辆控制指令redis通道
def carCmdChannel(groupid: str, car_id: str):
    return carCmdChannelPrefix(groupid) + '_' + car_id


# 车辆状态信息通道前缀(加上*号即可获取所有关联通道)
def carStateChannelPrefix(groupid: str):
    return str(groupid) + "_car_state"


# 车辆状态信息通道
def carStateChannel(groupid: str, car_id: str):
    return carStateChannelPrefix(groupid) + '_' + car_id


def userLogioChannel():
    return "user_logio"


# 用户上下线通知redis消息
def userLogioRedisMsg(user_type, group_id, user_id, login_time, is_login):
    msg = {'islogin': int(is_login), 'usertype': user_type, 'groupid': group_id,
           'userid': user_id, 'logintime': login_time}
    return json.dumps(msg)
