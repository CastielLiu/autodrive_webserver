import json
import threading

from apps.autodrive.datatypes import ChangeDataMonitor


# 车辆状态信息
class CarState:  # 车辆状态
    def __init__(self):
        self.speed = None
        self.steer_angle = None
        self.gear = None
        self.longitude = None
        self.latitude = None
        self.x = None
        self.y = None
        self.status = ChangeDataMonitor()
        self.mode = ChangeDataMonitor()

    def changed(self):
        return self.status.changed() or self.mode.changed()

    # 获取车辆状态数据字典
    def data(self):
        d = dict()
        d['speed'] = self.speed
        d['steer_angle'] = self.steer_angle
        d['gear'] = self.gear
        d['mode'] = self.mode
        d['longitude'] = self.longitude
        d['latitude'] = self.latitude
        return d

    def __str__(self):
        return json.dumps(self.data())


# 同步请求执行任务 (服务器向car客户端发送控制请求, 并同步等待响应)
class SyncRequestTask:
    def __init__(self):
        self.cv = threading.Condition()  # 请求执行任务的条件变量
        self.response = None


# websocketConsumer集合, 用户存储已登录到当前服务器的用户
# 每个服务器均订阅所有用户的上下线信息, 并在当前服务器列表中查看是否存在, 如果存在则迫使其下线
# 用户在A服务器登录, 而在B服务器用户列表中存在-> 迫使下线
# 用户在A服务器登录, 在A服务器用户列表中存在(必然存在), 不进行操作
# 判断是否为同一服务器的方式为login_flag是否相同, 相同则为同一服务器
class ClientConsumerSet:
    def __init__(self):
        self._consumers = dict()
        self._lock = threading.Lock()

    def __contains__(self, item):
        self._lock.acquire()
        is_in = item in self._consumers
        self._lock.release()
        return is_in

    # 添加元素 用户登录成功后添加
    def add(self, item, consumer):
        self._lock.acquire()
        if item in self._consumers:  # 用户已在当前服务器登录
            self._consumers[item].closeConnect('{"type": "rep_force_offline"}')
        
        self._consumers[item] = consumer  # 存储新的consumer
        self._lock.release()

    # 删除元素 用户退出登录或被迫退出登录时删除
    def remove(self, item):
        self._lock.acquire()
        if item in self._consumers:
            self._consumers.pop(item)
        self._lock.release()

    # 异处登录，强制下线
    def forceOffline(self, item, login_flag):
        self._lock.acquire()
        consumer = self._consumers.get(item)
        if consumer:
            if login_flag != consumer.login_flag:  # 登录标志与当前服务器所存储的不同, 即异处登录
                consumer.closeConnect('{"type": "rep_force_offline", "test": 0}')
        self._lock.release()

    def size(self):
        return len(self._consumers)
