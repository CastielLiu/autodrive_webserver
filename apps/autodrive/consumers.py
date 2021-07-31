# equal to views.py(视图函数) django
import json
import threading
import time

from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q, F

from apps.autodrive.ws_client.carclient import CarClient
from apps.autodrive.ws_client.webclient import UserClient

from .models import CarUser, WebUser
from .utils import userLoginCheck

g_test_clients = []
g_car_clients = dict()  # user_id:  client_object
g_user_clients = dict()  # user_id: client_object


# websocket消费者测试例
class TestConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        if self not in g_test_clients:
            g_test_clients.append(self)

        print("ws_client count: %d" % len(g_test_clients))

    def disconnect(self, close_code):
        if self in g_test_clients:
            g_test_clients.remove(self)
        print("ws_client count: %d" % len(g_test_clients))

    def receive(self, text_data):
        text_data_dict = json.loads(text_data)
        message = text_data_dict['message']

        self.send(text_data=json.dumps({
            'message': message
        }))


# 客户端消费者基类
class ClientConsumer(WebsocketConsumer):
    user_id = None
    user_name = None
    token = ""
    login_ok = False

    # 关闭连接, response: 关闭回应
    def closeConnect(self, response=None):
        if response:
            print("closeConnect", response)
            self.send(response)
        self.close()

    # 用户登录, 登录成功后将其加入用户列表
    # @param database: 用户信息数据库
    # @param data_dict: 用户请求登录数据
    # @param clients:   已登录客户端
    # @param client_type: 客户类型
    # @return res: 登录成功
    def login(self, database, data_dict, clients, client_type):
        responce = {"type": "res_login", "msg": {"result": False, "info": ""}}
        if self.login_ok:  # 重复登录
            responce["msg"]["result"] = True
            responce["msg"]["info"] = "重复登录"
            self.send(json.dumps(responce))
        else:  # 尚未登录
            user_id = data_dict.get("user_id", "")
            user_name = data_dict.get("username", "")
            password = data_dict.get("password", "")
            token = data_dict.get("token", "")

            login_res = userLoginCheck(database, user_id, user_name, password, token)

            responce["msg"]["result"] = login_res['ok']
            responce["msg"]["info"] = login_res['info']
            print(responce)
            self.send(json.dumps(responce))
            if not login_res['ok']:
                self.close()
                return False
            self.login_ok = True
            self.user_id = login_res['userid']
            self.user_name = login_res['username']

            # 当前车辆是否在客户端列表, 无则添加
            if self.user_id not in clients:
                clients[self.user_id] = client_type(self.user_id, self.user_name, self)
                print("new ws_client, id: %s, type: %s, total: %d" % (
                    self.user_id, clients[self.user_id].type, len(clients)))

        # 调用子类登录成功‘回调函数’(如果有)
        on_login = getattr(self, "on_login", None)
        if on_login:
            on_login()
        return True

    # 注销用户
    # clients 已登录用户列表
    def logout(self, clients):
        if self.login_ok and self.user_id in clients:
            client = clients.pop(self.user_id)
            print("user: %s logout, remaind %d %s users" % (self.user_id, len(clients), client.type))
        self.login_ok = False
        self.user_id = -1
        # 调用子类注销成功‘回调函数’(如果有)
        on_logout = getattr(self, "on_logout", None)
        if on_logout:
            on_logout()

    # 客户端消息预处理, 格式错误处理, 登录注销
    # @param text_data客户端消息
    # @param database: 用户信息数据库
    # @param clients:   已登录客户端
    # @param client_type: 客户类型
    # @return msg_type: 需要继续处理的消息类型
    # @return dict类型msg数据
    def preprocesse(self, text_data, database, clients, client_type):
        # 防止未登录客户大数据注入, 后续考虑添加高频非法访问屏蔽, 避免普通攻击
        if not self.login_ok and len(text_data) > 200:
            print("伪数据注入, 访问者未登录且传输大量数据")
            self.closeConnect("非法访问")
            return None, None

        # 数据格式校验
        try:
            data_dict = json.loads(text_data)
        except Exception as e:
            self.closeConnect("数据格式错误!")
            return None, None

        msg_type = data_dict.get('type', None)
        msg_dict = data_dict.get('msg', dict())

        if msg_type is None:  # 无type字段
            self.closeConnect("消息类型错误!")
        elif msg_type == "req_login":  # 登录请求
            self.login(database, msg_dict, clients, client_type)
        elif msg_type == "req_logout":  # 注销
            self.logout(clients)
        else:  # 其他消息类型
            if self.login_ok:  # 已经登录
                return msg_type, msg_dict  # 数据需继续处理
            else:  # 尚未登录
                self.closeConnect("非法访问!")

        return False, None  # 数据无需继续处理


# 车端客户端数据消费者
class CarClientsConsumer(ClientConsumer):

    # 重载父类方法 手动接受连接
    def connect(self):
        self.accept()

    # 重载父类方法
    def disconnect(self, close_code):
        self.logout(g_car_clients)

    # 重载父类方法
    def receive(self, text_data):
        # print(text_data)
        msg_type, msg = self.preprocesse(text_data, CarUser, g_car_clients, CarClient)
        if not msg_type:
            return

        if msg_type == "rep_car_state":
            client = g_car_clients[self.user_id]
            client.state.speed = msg.get("speed", None)
            client.state.steer_angle = msg.get("steer_angle", None)
            client.state.mode = msg.get("mode", None)

    def on_login(self):
        pass

    def on_logout(self):
        pass


# web端客户端
class UserClientConsumer(ClientConsumer):
    thread_run_flag = True
    report_thread = None

    # 需要监听的客户列表, 根据客户端请求进行配置
    # car_id: attrs[] # 需要监听的字段, 当为空时则监听所有字段
    listen_cars = {}

    # 数据报告线程, 将车辆数据按照一定频率转发到web客户端
    def reportThread(self):
        report = {"type": "rep_car_state", "msg": None}
        while self.thread_run_flag:
            try:
                for car_id, car_attrs in self.listen_cars.items():
                    if car_id not in g_car_clients:
                        continue
                    report['msg'] = g_car_clients[car_id].reltimedata(car_attrs)
                    self.send(json.dumps(report))
            except Exception as e:
                print("reportThread error", e)
            time.sleep(0.1)

    # 重载父类方法 手动接受连接
    def connect(self):
        self.accept()

    # 重载父类方法
    def disconnect(self, close_code):
        self.thread_run_flag = False
        self.logout(g_user_clients)

    # 重载父类方法
    def receive(self, text_data):
        print(text_data)
        response = {"type": "", "msg": ""}
        msg_type, msg = self.preprocesse(text_data, WebUser, g_user_clients, UserClient)
        if not msg_type:
            return

        if msg_type == "req_online_car":  # 请求获取在线车辆列表
            cars = []
            for car_id, car_client in g_car_clients.items():
                cars.append({"id": car_id, "name": car_client.name})

            response["type"] = "res_online_car"
            response["msg"] = {"cars": cars}
            # "msg": {"cars": [{"id": x, "name": x}]}
            self.send(json.dumps(response))

        elif msg_type == "req_listen_car":
            cars = msg.get("cars", dict())
            for car in cars:
                car_id = car.get("id")
                car_attr = car.get("attr")
                if car_id is None or car_attr is None:
                    continue
                if type(car_attr) != list:
                    continue
                if len(car_attr) == 0:  # 属性为空, 不再监听
                    if car_id in self.listen_cars:
                        self.listen_cars.pop(car_id)
                self.listen_cars[car_id] = car_attr

    def on_login(self):
        # 启动数据自动上报线程
        self.report_thread = threading.Thread(target=self.reportThread)
        self.report_thread.start()

    def on_logout(self):
        pass
