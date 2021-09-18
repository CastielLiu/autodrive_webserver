# 车辆客户端
import json
import threading

from django.conf import settings

from .client import Client
from ..datatypes import ChangeDataMonitor


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


# 请求执行任务
class RequestTask:
    def __init__(self):
        self.cv = threading.Condition()  # 请求执行任务的条件变量
        self.response = None


# 车辆客户端
class CarClient(Client):
    def __init__(self, car_id, car_name, ws):
        Client.__init__(self, "car", car_id, car_name, ws)
        self.state = CarState()
        self.reqest_task = RequestTask()

    # 获取车辆实时数据
    def reltimedata(self, attrs):
        d = dict()
        d['car_id'] = self.id
        d['car_state'] = self.state.data()
        return d
