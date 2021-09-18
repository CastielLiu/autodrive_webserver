import json

import redis, threading
from django.conf import settings


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

    def testCallback(self, item):
        print("test", item)

    # 添加订阅的通道
    def subscribe(self, *args, **kwargs):
        self.pubsub.subscribe(*args, **kwargs)
        if not self.pubsub_thread_started:
            self.pubsub.run_in_thread(1.0)
            self.pubsub_thread_started = True

    def unsubscribe(self, *args):
        self.pubsub.unsubscribe(*args)

    # 订阅一个或多个给定模式的通道
    def psubscribe(self, *args, **kwargs):
        self.pubsub.psubscribe(*args, **kwargs)
        if not self.pubsub_thread_started:
            self.pubsub.run_in_thread(1.0)
            self.pubsub_thread_started = True

    def punsubscribe(self, *args):
        self.pubsub.punsubscribe(*args)

    # 接收同步通道的信息
    def _onSyncMessage(self, item: dict):
        self.sync_cv.acquire()
        self.sync_msg = item['data']
        self.sync_cv.notify()
        self.sync_cv.release()
        self.pubsub.unsubscribe(item['channel'])  # 不再订阅

    # channel 发布通道
    # msg 发布消息
    # sync_channel 同步的通道(默认为None 无需同步), 订阅同步通道获取应答
    def publish(self, channel, msg, sync_channel=None, publisher=None, timeout=0):
        result = dict()
        if publisher:
            result['pub'] = publisher
        if sync_channel:
            result['sync'] = sync_channel
        result['msg'] = msg
        self.client.publish(channel, json.dumps(result))
        if sync_channel:
            self.sync_cv.acquire()
            self.pubsub.subscribe(**{sync_channel: self._onSyncMessage})
            if self.sync_cv.wait(timeout):
                return self.sync_msg
        return None











