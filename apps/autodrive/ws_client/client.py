# 客户端
from django.db.models import Q, F
from random import Random
import string


# ws客户端基类
class Client:
    def __init__(self, _type, _id, _name, _ws):
        self.type = _type  # 客户端用户类型
        self.id = _id  # 客户端用户id
        self.ws = _ws  # 客户端websocket
        self.name = _name  # 客户端用户名称

    def close(self):
        self.ws.close()
