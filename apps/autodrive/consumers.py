# equal to views.py(视图函数) django

import json
import threading
import time

from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from apps.autodrive.ws_client.carclient import CarClient
from apps.autodrive.ws_client.webclient import UserClient
from .models import CarUser, WebUser
from .redis_pubsub import PubSub
from .utils import *

g_car_clients = dict()  # user_id:  client_object(用户信息+ws)
g_user_clients = dict()  # user_id: client_object(用户信息+ws)
g_pubsub = PubSub()


# 客户端消费者基类
class ClientConsumer(WebsocketConsumer):
    CAR_CLIENT_TYPE = 0
    WEB_CLIENT_TYPE = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_groupname = None
        self.user_groupid = None
        self.user_id = None
        self.user_name = None
        self.token = ""
        self.login_ok = False
        self.client = None  # 客户端数据
        self.client_type = None
        self.db = None  # 数据库

    def safetySend(self, text_data=None, bytes_data=None, close=False):
        try:
            self.send(text_data, bytes_data, close)
        except Exception as e:
            if not self.login_ok:
                return

            if self.login_ok:  # 发送失败且已登录, 则自动退出登录
                self.logout()

    # 关闭连接, response: 关闭回应
    def closeConnect(self, response=None):
        if response:
            debug_print("closeConnect", response)
            self.send(response)
        self.close()

    # 用户登录, 登录成功后将其加入用户列表
    # @param data_dict: 用户请求登录数据
    # @param clients:   已登录客户端
    # @param client_type: 客户类型
    # @return res: 登录成功
    def login(self, data_dict, clients, client_type):
        responce = {"type": "res_login", "code": 0, "msg": "", "data": {}}
        if self.login_ok:  # 重复登录
            responce["code"] = 0
            responce["msg"] = "重复登录"
            self.send(json.dumps(responce))
        else:  # 尚未登录,进行验证
            user_id = data_dict.get("userid", "")
            user_name = data_dict.get("username", "")
            password = data_dict.get("password", "")
            token = data_dict.get("token", "")

            login_res = userLoginCheck(self.db, user_id, user_name, password, token)
            print("ws_login_res", login_res)
            if login_res['ok']:
                responce["code"] = 0
                responce["msg"] = login_res['info']
                debug_print("login check.", responce)
                self.send(json.dumps(responce))
            else:
                responce["code"] = 1
                responce["msg"] = login_res['info']
                self.closeConnect(json.dumps(responce))
                return False

            self.login_ok = True
            self.user_id = str(login_res['userid'])
            self.user_name = login_res['username']
            self.user_groupname = login_res['group']
            self.user_groupid = str(login_res['groupid'])

            # 此处直接在本地列表中进行的查找, 服务器集群时应当广播用户上线信息, 若在其他服务器已登录，强迫下线
            if self.user_id in clients:  # 用户已在列表, 断开历史连接
                clients[self.user_id].ws.closeConnect('{"type": "rep_force_offline"}')  # 被迫下线

            # 当前车辆是否在客户端列表, 有则覆盖, 无则添加
            clients[self.user_id] = self.client = client_type(self.user_id, self.user_name, self)
            debug_print("new ws_client connect, id: %s, type: %s, total: %d" % (
                self.user_id, clients[self.user_id].type, len(clients)))

        # 调用子类登录成功‘回调函数’(如果有)
        on_login = getattr(self, "on_login", None)
        if on_login:
            on_login()

        # print("login: ", self.login_ok, data_dict)
        return True

    # 注销用户
    # clients 已登录用户列表
    def logout(self, clients):
        if self.login_ok and self.user_id in clients:
            client = clients.pop(self.user_id)
            print("user: %s logout, remaind %d %s users" % (self.user_id, len(clients), client.type))
        userLogout(self.db, self.user_name, update_db=True)  # 在数据库中标注离线
        self.login_ok = False
        self.closeConnect()
        # 调用子类注销成功‘回调函数’(如果有)
        on_logout = getattr(self, "on_logout", None)
        if on_logout:
            on_logout()

    # 客户端消息预处理, 格式错误处理, 登录注销
    # @param text_data客户端消息
    # @param clients:   已登录客户端
    # @param client_type: 客户类型
    # @return msg_type: 需要继续处理的消息类型
    # @return dict类型msg数据
    def preprocesse(self, text_data, clients, client_type):
        # debug_print("ws preprocesse: %s" % text_data)
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
        msg_dict = data_dict.get('data', dict())

        if msg_type is None:  # 无type字段
            self.closeConnect("消息类型错误!")
        elif msg_type == "req_login":  # 登录请求
            ok = self.login(msg_dict, clients, client_type)
        elif msg_type == "req_logout":  # 注销
            self.logout(clients)
        else:  # 其他消息类型
            if not self.login_ok:  # 未登录,非法访问
                self.closeConnect("非法访问!")
            # 记录的websocket 与当前websocket不同时
            # 已被其他连接覆盖(关键)
            elif clients.get(self.user_id).ws != self:
                self.closeConnect()
            else:  # 已经登录
                return msg_type, msg_dict  # 数据需继续处理

        return None, None  # 数据无需继续处理

    def on_received(self, text_data):
        # debug_print("consumer线程id: %d, 总线程数: %d" % (threading.currentThread().ident, len(threading.enumerate())))
        # self.send("server received %s" % text_data)
        # debug_print("ws_receive: ", text_data)
        pass


# 车端客户端数据消费者
class CarClientsConsumer(ClientConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.car_state_channel = None
        self.car_cmd_channel = None
        self.client = None
        self.client_type = self.CAR_CLIENT_TYPE
        self.db = CarUser

    # 重载父类方法 手动接受连接
    def connect(self):
        self.accept()

    # 重载父类方法
    def disconnect(self, close_code):
        # 车端客户断开链接时自动注销
        self.logout(g_car_clients)

    # 重载父类方法
    def receive(self, text_data):
        self.on_received(text_data)

        msg_type, msg = self.preprocesse(text_data, g_car_clients, CarClient)

        if msg_type is None:
            return
        if msg_type == "rep_car_state":  # 车端向服务器上报状态信息, 服务器向web端转发并定时保存到数据库
            self.client.state.speed = msg.get("speed", None)
            self.client.state.steer_angle = msg.get("steer_angle", None)
            self.client.state.longitude = msg.get("lng", None)
            self.client.state.latitude = msg.get("lat", None)

            self.client.state.mode.set(msg.get("mode", None))
            self.client.state.status.set(msg.get("status", 'unknown'))

            # 广播车辆状态信息
            g_pubsub.publish(channel=self.car_state_channel, msg=text_data)

            # 控制数据写数据库的频率
            now = time.time()
            if not hasattr(self, "last_data_save_time") \
                    or now - self.last_data_save_time >= 1.0 \
                    or self.client.state.changed():
                try:
                    # 将部分数据存到数据库
                    car_user = self.db.objects.get(userid=self.client.id)
                    car_user.longitude = self.client.state.longitude
                    car_user.latitude = self.client.state.latitude
                    car_user.system_state = self.client.state.status.get()
                    car_user.save()
                    self.last_data_save_time = now
                except Exception as e:
                    print(e)

        # 车端回应任务请求
        elif msg_type == "res_start_task" or \
                msg_type == "res_stop_task":  # 车端回应任务请求
            print(msg_type, msg_type, msg_type)
            self.client.reqest_task.cv.acquire()
            self.client.reqest_task.response = text_data
            self.client.reqest_task.cv.notify()
            self.client.reqest_task.cv.release()
        elif msg_type == "rep_taskdone" or \
                msg_type == "rep_taskfeedback":
            # 转发到web客户端
            g_pubsub.publish(channel=self.car_state_channel, msg=msg)
        else:
            print("Unknown msg type: %s!" % msg_type)

    # 接收经redis转发的车辆控制请求指令
    def redisCarCmdCallback(self, item: dict):
        data_dict = json.loads(item['data'])
        sync_channel = data_dict.get('sync')  # 请求的同步响应通道(指令发送者期望通过该通道获取响应)
        error_msg = None
        try:
            self.send(text_data=data_dict.get('body'))  # 转发cmd到车端
            send_ok = True
        except Exception as e:
            send_ok = False
            error_msg = "Communation with car error"

        if sync_channel is None:  # 无需同步响应
            return

        print("redisCarCmdCallback", data_dict)
        sync_timeout = data_dict.get('timeout', 0)
        self.client.reqest_task.cv.acquire()
        gotit = self.client.reqest_task.cv.wait(sync_timeout)
        if not gotit:
            error_msg = "Request timeout in driverless server."

        print("self.client.reqest_task.response", self.client.reqest_task.response)
        g_pubsub.sync_response(sync_channel, self.client.reqest_task.response, error_msg)
        self.client.reqest_task.response = ""
        self.client.reqest_task.cv.release()

    def on_login(self):
        # car用户登录成功后, 添加redis订阅
        self.car_cmd_channel = carCmdChannel(self.user_groupid, self.user_id)
        self.car_state_channel = carStateChannel(self.user_groupid, self.user_id)

        # 订阅针对当前car用户的通道(唯一订阅者->唯一回调函数)
        g_pubsub.subscribe(self.car_cmd_channel, self.redisCarCmdCallback)

    def on_logout(self):
        g_pubsub.unsubscribe(self.car_cmd_channel)
        pass


# web端客户端
class WebClientConsumer(ClientConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thread_run_flag = True
        self.report_thread = None
        self.client_type = self.WEB_CLIENT_TYPE
        self.db = WebUser
        # 需要监听的客户列表, 根据客户端请求进行配置
        # car_id: attrs[] # 需要监听的字段, 当为空时则监听所有字段
        self.listen_cars = {}

    # 数据报告线程, 将车辆数据按照一定频率转发到web客户端
    def reportThread(self):
        report = {"type": "rep_car_state", "data": {}}
        while self.thread_run_flag:
            try:
                for car_id, car_attrs in self.listen_cars.items():
                    if car_id not in g_car_clients:
                        continue
                    report['data'] = g_car_clients[car_id].reltimedata(car_attrs)
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

        # web用户webSocket断开连接时不注销用户, 防止用户刷新页面后token失效
        # 仅当请求注销时进行注销
        # self.logout(g_user_clients)

    # 重载父类方法
    def receive(self, text_data):
        self.on_received(text_data)

        msg_type, msg = self.preprocesse(text_data, g_user_clients, UserClient)
        if msg_type is None:
            return
        response = {"type": msg_type.replace("req", "res"), "msg": "", "code": 0, "data": {}}

        if msg_type == "req_car_list":  # 请求获取车辆列表
            cars = []
            for car_id, car_client in g_car_clients.items():
                cars.append({"id": car_id, "name": car_client.name})

            response["data"] = {"cars": cars}
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
        else:
            self.send("Unknown request type!")

    # 车辆状态信息(组内用户)
    def redisCarStateCallback(self, item):
        print("web user %s sub car state:" % self.user_name, item)
        data_dict = json.loads(item['data'])
        try:
            self.send(text_data=data_dict.get('body'))  # 转发数据转发到web客户端
        except Exception as e:
            pass

    def on_login(self):
        # 启动数据自动上报线程
        self.report_thread = threading.Thread(target=self.reportThread)
        self.report_thread.start()

        # 订阅组内car用户所有状态信息
        g_pubsub.psubscribe(carStateChannelPrefix(self.user_groupid)+'*', self.redisCarStateCallback, self.user_id)

    def on_logout(self):
        g_pubsub.punsubscribe(carStateChannelPrefix(self.user_groupid)+'*', self.user_id)

