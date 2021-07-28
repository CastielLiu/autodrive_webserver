# equal to views.py(视图函数) django
import json
import threading
import time

from channels.generic.websocket import WebsocketConsumer

from apps.autodrive.client.carclient import CarClient
from apps.autodrive.client.webclient import UserClient
from apps.autodrive.client.client import login

from .models import CarUser, WebUser

g_test_clients = []
g_car_clients = dict()   # user_id: object
g_user_clients = dict()  # user_id: object


# websocket消费者测试例
class TestConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        if self not in g_test_clients:
            g_test_clients.append(self)

        print("client count: %d" % len(g_test_clients))

    def disconnect(self, close_code):
        if self in g_test_clients:
            g_test_clients.remove(self)
        print("client count: %d" % len(g_test_clients))

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        self.send(text_data=json.dumps({
            'message': message
        }))


# 车端客户端数据消费者
class CarClientsConsumer(WebsocketConsumer):
    user_id = None
    login_ok = False  # 是否已登录

    # 重载父类方法 手动接受连接
    def connect(self):
        self.accept()

    # 重载父类方法
    def disconnect(self, close_code):
        if self.user_id in g_car_clients:
            client = g_car_clients.pop(self.user_id)

        print("car client count: %d" % len(g_car_clients))

    # 重载父类方法
    def receive(self, text_data):
        print(text_data)
        try:
            data_json = json.loads(text_data)
        except Exception as e:
            self.send("数据格式错误")
            self.close()
            return

        if not self.login_ok:  # 尚未登录
            ok, msg, self.user_id = login(CarUser, data_json)
            result = {"login": ok, "msg": msg}
            self.send(json.dumps(result))
            if not ok:
                self.close()
                return

            self.login_ok = True

            # 当前车辆是否在客户端列表, 无则添加
            if self.user_id not in g_car_clients:
                g_car_clients[self.user_id] = CarClient(self.user_id, self)
                print("new car, id: %s" % self.user_id)
                print("car client count: %d" % len(g_car_clients))
            return

        client = g_car_clients[self.user_id]
        client.state.speed = data_json.get("speed", None)
        client.state.steer_angle = data_json.get("steer_angle", None)
        client.state.mode = data_json.get("mode", None)

        # print(client.state)


# web端客户端
class UserClientConsumer(WebsocketConsumer):
    user_id = -1
    login_ok = False
    thread_run_flag = True
    report_thread = None

    def reportThread(self):
        while self.thread_run_flag:
            try:
                for user_id, car_client in g_car_clients.items():
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

        print("client client count: %d" % len(g_user_clients))

    # 重载父类方法
    def receive(self, text_data):
        # print(text_data)
        try:
            data_json = json.loads(text_data)
        except Exception as e:
            self.send("数据格式错误")
            self.close()
            return

        if not self.login_ok:  # 尚未登录
            ok, msg, self.user_id = login(WebUser, data_json)
            result = {"login": ok, "msg": msg}
            self.send(json.dumps(result))
            if not ok:
                self.close()
                return
            self.login_ok = True

            # 当前车辆是否在客户端列表, 无则添加
            if self.user_id not in g_user_clients:
                g_user_clients[self.user_id] = UserClient(self.user_id, self)
                # 启动数据自动上报线程
                self.report_thread = threading.Thread(target=self.reportThread)
                self.report_thread.start()
                print("new client, id: %s" % self.user_id)
                print("client client count: %d" % len(g_user_clients))
                return
