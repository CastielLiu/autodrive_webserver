# equal to views.py(视图函数) django
import json
import threading
import time

from channels.generic.websocket import WebsocketConsumer

from apps.autodrive.user.caruser import CarClient
from apps.autodrive.user.webuser import UserClient

from .models import CarUser, WebUser

g_test_clients = []
g_car_clients = dict()   # car_id: object
g_user_clients = dict()  # user_id: object


# websocket消费者测试例
class TestConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        if self not in g_test_clients:
            g_test_clients.append(self)

        print("user count: %d" % len(g_test_clients))

    def disconnect(self, close_code):
        if self in g_test_clients:
            g_test_clients.remove(self)
        print("user count: %d" % len(g_test_clients))

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        self.send(text_data=json.dumps({
            'message': message
        }))


# 车端客户端数据消费者
class CarClientsConsumer(WebsocketConsumer):
    car_id = None
    login = False  # 是否已登录

    # 重载父类方法 手动接受连接
    def connect(self):
        self.accept()

    # 重载父类方法
    def disconnect(self, close_code):
        if self.car_id in g_car_clients:
            client = g_car_clients.pop(self.car_id)

        print("car user count: %d" % len(g_car_clients))

    def userCheck(self, info):
        pass

    # 重载父类方法
    def receive(self, text_data):
        # print(text_data)
        data_json = json.loads(text_data)

        # 此处应通过数据库查找帐号密码, 如不匹配, 断开链接
        self.car_id = data_json.get("car_id", None)
        if self.car_id is None or self.car_id == "":  # or not isinstance(self.car_id, type(self.car_id)):
            self.close()
            return
        elif not self.login:  # 尚未登录
            # user_name = data_json.get("user_name", None)
            # passwd = data_json.get("passwd", None)
            # if user_name is None or passwd is None:
            #     self.close()
            #     return
            # try:
            #     user = CarUser.objects.get(name=user_name, is_active=True)
            # except Exception as e:
            #     self.send("用户不存在")
            #     self.close()
            #     return
            # if user.passwd != passwd:
            #     self.send("密码错误")
            #     self.close()
            #     return
            self.login = True
            # 当前车辆是否在客户端列表, 无则添加
            if self.car_id not in g_car_clients:
                g_car_clients[self.car_id] = CarClient(self.car_id, self)
                print("new car, id: %s" % self.car_id)
                print("car user count: %d" % len(g_car_clients))

        client = g_car_clients[self.car_id]
        client.state.speed = data_json.get("speed", None)
        client.state.steer_angle = data_json.get("steer_angle", None)
        client.state.mode = data_json.get("mode", None)

        # print(user.state)


# web端客户端
class UserClientConsumer(WebsocketConsumer):
    user_id = -1
    thread_run_flag = True
    report_thread = None

    def reportThread(self):
        while self.thread_run_flag:
            try:
                for car_id, car_client in g_car_clients.items():
                    # print(car_client.reltimedata())
                    self.send(json.dumps(car_client.reltimedata()))
            except Exception as e:
                print(e)
            time.sleep(0.1)

    # 重载父类方法 手动接受连接
    def connect(self):
        self.accept()

    # 重载父类方法
    def disconnect(self, close_code):
        self.thread_run_flag = False
        if self.user_id in g_user_clients:
            client = g_user_clients.pop(self.user_id)

        print("user user count: %d" % len(g_user_clients))

    # 重载父类方法
    def receive(self, text_data):
        # print(text_data)
        data_json = json.loads(text_data)
        self.user_id = data_json.get("user_id", None)
        if self.user_id is None or self.user_id == "":  # or not isinstance(self.user_id, type(self.user_id)):
            self.close()
            return

        # 当前车辆是否在客户端列表, 无则添加
        if self.user_id not in g_user_clients:
            g_user_clients[self.user_id] = UserClient(self.user_id, self)
            # 启动数据自动上报线程
            self.report_thread = threading.Thread(target=self.reportThread)
            self.report_thread.start()
            print("new user, id: %s" % self.user_id)
            print("user user count: %d" % len(g_user_clients))
