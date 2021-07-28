# 车辆客户端
import json

from .user import Client


# 车辆状态
class CarState:
    def __init__(self):
        self.speed = None
        self.steer_angle = None
        self.gear = None
        self.mode = None
        self.longitude = None
        self.latitude = None

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


# 车辆客户端
class CarClient(Client):
    def __init__(self, car_id, ws):
        Client.__init__(self, car_id, ws)
        self.state = CarState()

    # 获取车辆实时数据
    def reltimedata(self):
        d = dict()
        d['car_id'] = self.id
        d['car_state'] = self.state.data()
        return d
