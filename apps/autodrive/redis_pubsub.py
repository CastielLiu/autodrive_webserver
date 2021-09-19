import json

import redis, threading
from django.conf import settings

# 自定义redis通信线路协议
# 请求 request = {'sync': str, 'timeout': float, 'body': str} sync同步响应通道, timeout响应超时时间, body请求体
# 应答 response = {'ok': bool, 'body': str} ok请求是否成功, body响应体
# 汇报 report = {'body': str} body汇报体


class PubSub:
    def __init__(self):
        self.pool = redis.ConnectionPool(host=settings.REDIS['HOST'], port=settings.REDIS['PORT'],
                                         db=settings.REDIS['DB'], password=settings.REDIS['PASSWORD'])
        self.client = redis.StrictRedis(connection_pool=self.pool)
        self.pubsub = self.client.pubsub()
        self.pubsub.ping()
        self.pubsub_thread_started = False

        self.sync_cv = threading.Condition()
        self.sync_msg = ""

    # 添加订阅的通道
    def subscribe(self, channel, callback):
        self.pubsub.subscribe(**{channel: callback})
        if not self.pubsub_thread_started:
            self.pubsub.run_in_thread(1.0)
            self.pubsub_thread_started = True

    def unsubscribe(self, channel):
        self.pubsub.unsubscribe(channel)

    # 订阅一个或多个给定模式的通道
    def psubscribe(self, channel, callback):
        self.pubsub.psubscribe(**{channel: callback})
        if not self.pubsub_thread_started:
            self.pubsub.run_in_thread(1.0)
            self.pubsub_thread_started = True

    def punsubscribe(self, channel):
        self.pubsub.punsubscribe(channel)

    # channel 发布通道
    # msg 发布消息
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
        request = {'sync': sync_channel, 'timeout': timeout, 'body': msg}

        self.sync_cv.acquire()
        self.subscribe(sync_channel, self._onSyncMessage)
        self.client.publish(channel, json.dumps(request))
        if self.sync_cv.wait(timeout):
            self.sync_cv.release()
            return self.sync_msg

        self.sync_cv.release()
        return None

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











