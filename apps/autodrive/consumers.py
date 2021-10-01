# equal to views.py(视图函数) django

import json
import threading
import time

from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from .models import CarUser, WebUser
from .redis_pubsub import *
from .structs import *
from .utils import *

g_pubsub = PubSub()
g_carConsumers = ClientConsumerSet()
g_webConsumers = ClientConsumerSet()
instance_cnt = 0

"""
Websocket是民主的, 建立连接时需要握手协议,而断开连接时需要通知客户端让对方自己断开, 因此服务端调用close并不能断开连接
"""


# 客户端消费者基类
class ClientConsumer(WebsocketConsumer):
    CAR_USER_TYPE = CarUser().type
    WEB_USER_TYPE = WebUser().type

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_groupname = None
        self.user_groupid = None
        self.user_id = None
        self.user_name = None
        self.token = ""
        self.login_ok = False
        self.login_time = None  # 以字符串形式存储
        self.login_flag = ""  # 登录标志字符串, 用在登录通知消息体中,区分不同的登录
        self.user_type = None
        self.db = None  # 数据库
        self.send_lock = threading.Lock()  # 发送数据线程锁
        self.consumers = None  # WebsocketConsumer集合
        self.connected = False

        # global instance_cnt
        # instance_cnt = instance_cnt + 1
        # print("ClientConsumer constructed ", instance_cnt)

    def __del__(self):
        # global instance_cnt
        # instance_cnt = instance_cnt - 1
        # print("%s_%s ClientConsumer deconstructed" % (self.user_type, self.user_name))
        pass

    # 重载父类方法 手动接受连接
    def connect(self):
        self.accept()
        self.connected = True

    def receive(self, text_data=None, bytes_data=None):
        try:
            self.on_received(text_data, bytes_data)
        except AttributeError as e:
            debug_print("AttributeError: %s" % e)

    # 重载父类方法
    def disconnect(self, close_code):
        self.connected = False
        self.login_ok = False
        self.consumers.remove(self.user_id, self)
        self.logout()  # 自动退出登录

        debug_print("%s_%s disconnect. remaind %d %s users." % (self.user_type, self.user_name, self.consumers.size(), self.user_type))

        try:
            self.on_disconnect(close_code)
        except AttributeError as e:
            debug_print("AttributeError: %s" % e)

    # 以安全模式发送数据
    # 1. 确保用户已登录
    # 2. 加锁发送, 防止多线程冲突
    # 3. 异常捕获
    def safetySend(self, text_data=None, bytes_data=None, close=False):
        if not self.connected:
            return False

        ok = True
        try:
            self.send_lock.acquire()
            self.send(text_data, bytes_data, close)
        except Exception as e:
            debug_print("safetySend '%s' failed: %s" % (text_data, e))
            ok = False
        finally:
            self.send_lock.release()

        return ok

    # 关闭连接, response: 关闭回应
    # 发送关闭连接信号到客户端,由客户端发起断开请求
    def closeConnect(self, response=None):
        if response:
            # print("closeConnect", response)
            self.safetySend(response)
        self.safetySend(text_data=json.dumps({"type": "disconnect", "msg": ""}))

    # 强制下线
    def forceOffline(self):
        self.safetySend(text_data=json.dumps({"type": "rep_force_offline", "msg": ""}))

    # 用户登录, 登录成功后将其加入用户列表
    # @param data_dict: 用户请求登录数据
    # @return res: 登录成功
    def login(self, data_dict):
        response = {"type": "res_login", "code": 0, "msg": "", "data": {}}
        if self.login_ok:  # 重复登录
            response["code"] = 0
            response["msg"] = "重复登录"
        else:  # 尚未登录,进行验证
            user_id = data_dict.get("userid", "")
            user_name = data_dict.get("username", "")
            password = data_dict.get("password", "")
            token = data_dict.get("token", "")

            login_res = userLoginCheck(self.db, user_id, user_name, password, token)
            # print("ws_login_res", login_res)
            if login_res['ok']:
                response["code"] = 0
                response["msg"] = login_res['info']
            else:
                response["code"] = 1
                response["msg"] = login_res['info']
                self.closeConnect(json.dumps(response))
                return False

            self.login_ok = True
            self.login_time = login_res['logintime']
            self.user_id = str(login_res['userid'])
            self.user_name = login_res['username']
            self.user_groupname = login_res['group']
            self.user_groupid = str(login_res['groupid'])
        self.safetySend(json.dumps(response))

        # 调用子类登录成功‘回调函数’(如果有)
        # on_login = getattr(self, "on_login", None)
        # if on_login:
        #     on_login()
        try:
            self.on_login()
        except AttributeError as e:
            debug_print("AttributeError: %s" % e)

        # 以广播形式通知用户上线时, 所有服务器(包括当前服务器)将收到通知, 若通知的用户已在当前服务器登录, 则做下线处理
        # 但当前服务器若收到自己的通知消息, 则不做处理. 否则将导致刚登录的用户被下线
        # 登录标志字符串用于区分是否为自我发送
        # self.login_flag = str(time.time()) + '_' + randomStr(5)
        debug_print("user login, publish...")
        g_pubsub.publish(userLogioChannel(),
                         userLogioRedisMsg(self.user_type, self.user_groupid, self.user_id, self.login_time, True))
        debug_print("user login, add to consumers...")
        self.consumers.add(self.user_id, self)

        # print("login: ", self.login_ok, data_dict)
        return True

    # 注销用户
    def logout(self):
        if self.login_ok:
            if self.user_id in self.consumers:
                self.consumers.remove(self.user_id)  # 从集合中删除
                print("user: %s logout, remaind %d %s users" % (self.user_id, self.consumers.size(), self.user_type))
        else:  # 已经离线, 无需重复执行 (当连接断开时, 将自动调用退出登录)
            return

        userLogout(self.db, self.user_name, login_time=self.login_time)

        # 先将login_ok复位, 再关闭连接, 防止循环调用
        self.login_ok = False
        self.close()  # 关闭连接

        # 调用子类注销成功‘回调函数’(如果有)
        # on_logout = getattr(self, "on_logout", None)
        # if on_logout:
        #     on_logout()
        try:
            self.on_logout()
        except AttributeError as e:
            debug_print("AttributeError: %s" % e)
        g_pubsub.publish(userLogioChannel(),
                         userLogioRedisMsg(self.user_type, self.user_groupid, self.user_id, self.login_flag,
                                           False))  # 下线通知

    # 客户端消息预处理, 格式错误处理, 登录注销
    # @param text_data客户端消息
    # @return msg_type: 需要继续处理的消息类型
    # @return dict类型data数据
    def preprocesse(self, text_data):
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
            ok = self.login(msg_dict)
        elif msg_type == "req_logout":  # 注销
            self.logout()
        else:  # 其他消息类型
            if not self.login_ok:  # 未登录,非法访问
                self.closeConnect("非法访问!")
            else:  # 已经登录
                return msg_type, msg_dict  # 数据需继续处理

        return None, None  # 数据无需继续处理


# 车端客户端数据消费者
class CarClientsConsumer(ClientConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.car_state_channel = None  # 车辆状态数据通道
        self.car_cmd_channel = None  # 车辆调度控制指令通道
        self.user_type = self.CAR_USER_TYPE
        self.db = CarUser
        self.consumers = g_carConsumers

        self.state = CarState()  # 车辆状态
        self.sync_req_cv = threading.Condition()  # 同步请求条件变量
        self.sync_req_response = ""  # 同步请求应答结果

    def on_disconnect(self, close_code):
        pass

    # 重载父类方法
    def on_received(self, text_data, bytes_data):
        msg_type, msg = self.preprocesse(text_data)
        if msg_type is None:
            return
        if msg_type == "rep_car_state":  # 车端向服务器上报状态信息, 服务器向web端转发并定时保存到数据库
            self.state.speed = msg.get("speed", None)
            self.state.steer_angle = msg.get("steer_angle", None)
            self.state.longitude = msg.get("lng", None)
            self.state.latitude = msg.get("lat", None)

            self.state.mode.set(msg.get("mode", None))
            self.state.status.set(msg.get("status", 'unknown'))

            # redis广播车辆状态信息
            g_pubsub.publish(channel=self.car_state_channel, msg=text_data)

            # 控制数据写数据库的频率
            now = time.time()
            if not hasattr(self, "last_data_save_time") \
                    or now - self.last_data_save_time >= 1.0 \
                    or self.state.changed():
                try:
                    # 将部分数据存到数据库
                    car_user = self.db.objects.get(userid=self.user_id)
                    car_user.longitude = self.state.longitude
                    car_user.latitude = self.state.latitude
                    car_user.system_state = self.state.status.get()
                    car_user.save()
                    self.last_data_save_time = now
                except Exception as e:
                    print(e)
        # 车端回应任务请求
        elif msg_type == "res_start_task" or \
                msg_type == "res_stop_task":  # 车端回应任务请求
            # 收到车端对任务请求的响应, 唤醒请求线程进行通知
            self.sync_req_cv.acquire()
            self.sync_req_response = text_data
            self.sync_req_cv.notify()
            self.sync_req_cv.release()
        elif msg_type == "rep_taskdone" or \
                msg_type == "rep_taskfeedback":
            # 转发到web客户端
            g_pubsub.publish(channel=self.car_state_channel, msg=msg)  # this msg is dict
        else:
            print("Unknown msg type: %s!" % msg_type)

    # 接收经redis转发的车辆控制请求指令
    def redisCarCmdCallback(self, item: dict):
        data_dict = json.loads(item['data'])
        sync_channel = data_dict.get('sync')  # 请求的同步响应通道(指令发送者期望通过该通道获取响应)
        error_msg = None

        body = data_dict.get('body')
        if isinstance(body, dict):
            send_ok = self.safetySend(text_data=json.dumps(body))
        else:
            send_ok = self.safetySend(text_data=data_dict.get('body'))  # 转发cmd到车端

        if sync_channel is None:  # 无需同步响应
            return

        print("redisCarCmdCallback", data_dict)

        self.sync_req_cv.acquire()
        if not send_ok:
            error_msg = "Communation with car error"
        else:
            sync_timeout = data_dict.get('timeout', 0)
            gotit = self.sync_req_cv.wait(sync_timeout)
            if not gotit:
                error_msg = "Request timeout in driverless server."

        print("self.sync_req_response: ", self.sync_req_response)
        g_pubsub.sync_response(sync_channel, self.sync_req_response, error_msg)
        self.sync_req_response = ""
        self.sync_req_cv.release()

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
        self.user_type = self.WEB_USER_TYPE
        self.db = WebUser
        self.consumers = g_webConsumers
        # 需要监听的客户列表, 根据客户端请求进行配置
        self.sub_cars_list = {}  # {'carid': True/False}

    # 数据报告线程, 将车辆数据按照一定频率转发到web客户端
    def debugReportThread(self):
        report = {"type": "rep_car_state", "data": {}}
        while self.thread_run_flag:
            # try:
            #     for car_id, car_attrs in self.listen_cars.items():
            #         if car_id not in xx:
            #             continue
            #         report['data'] = xx[car_id].reltimedata(car_attrs)
            #         self.safetySend(json.dumps(report))
            # except Exception as e:
            #     print("debugReportThread error", e)
            time.sleep(0.1)

    def on_disconnect(self, close_code):
        self.thread_run_flag = False
        # web用户webSocket断开连接时不注销用户, 防止用户刷新页面后token失效
        # 仅当请求注销时进行注销
        # self.logout()

    # 重载父类方法
    def on_received(self, text_data, bytes_data):
        msg_type, data = self.preprocesse(text_data)
        if msg_type is None:
            return
        response = {"type": msg_type.replace("req", "res"), "msg": "", "code": 0, "data": {}}
        response_text = None

        if msg_type == "req_sub_car_state":
            action = data.get("action", "")
            cars_id = data.get("cars_id", [])
            if action == "ADD":  # 新增
                for carid in cars_id:
                    if carid == "*":  # 添加所有
                        cars = queryCarsInGroup(self.user_groupid)
                        for car in cars:
                            self.sub_cars_list[carid] = True
                        break
                    else:
                        self.sub_cars_list[carid] = True
            elif action == "DELETE":  # 删除
                for carid in cars_id:
                    if carid in self.sub_cars_list:
                        if carid == "*":  # 删除所有
                            self.sub_cars_list.clear()
                            break
                        else:
                            self.sub_cars_list.pop(carid)
            elif action == "REPLACE":  # 替换列表
                self.sub_cars_list.clear()
                for carid in cars_id:
                    self.sub_cars_list[carid] = True
            else:
                response['code'] = 1
                response['msg'] = "request action %s is invalid!" % action

            # 使用私有pubsub便于管理
            private_ps = self.user_id + "carState_ps"
            # 先取消所有订阅
            g_pubsub.unsubscribe(channel="", private_ps=private_ps, _all=True)
            # 再添加到redis订阅
            for carid in self.sub_cars_list:
                g_pubsub.subscribe(carStateChannel(self.user_groupid, carid),
                                   self.redisCarStateCallback, private_ps=private_ps)

            response['data'] = {"cars_id": self.sub_cars_list.keys()}
        else:
            self.safetySend("Unknown request type!")

        if response_text is not None:
            self.safetySend(response_text)
        else:
            self.safetySend(json.dumps(response))

    # 车辆状态信息(组内用户)
    def redisCarStateCallback(self, item):
        # print("web user %s sub car state:" % self.user_name, item)
        data_dict = json.loads(item['data'])

        body = data_dict.get('body')
        # 转发数据转发到web客户端
        if isinstance(body, dict):
            send_ok = self.safetySend(text_data=json.dumps(body))
        else:
            send_ok = self.safetySend(text_data=data_dict.get('body'))

    def on_login(self):
        # 启动数据自动上报线程
        self.report_thread = threading.Thread(target=self.debugReportThread)
        self.report_thread.start()

        # 订阅组内car用户所有状态信息
        g_pubsub.psubscribe(carStateChannelPrefix(self.user_groupid) + '*', self.redisCarStateCallback,
                            private_ps=self.user_id)

    def on_logout(self):
        g_pubsub.punsubscribe(carStateChannelPrefix(self.user_groupid) + '*', self.user_id)


# 用户上下线通知回调函数
def userLoginLogoutInfoCallback(item):
    try:
        redis_data = json.loads(item['data'])
        loginout_data = json.loads(redis_data['body'])
        islogin = loginout_data['islogin']  # login or logout
        usertype = loginout_data['usertype']
        groupid = loginout_data['groupid']
        userid = loginout_data['userid']
        login_time = loginout_data['logintime']
    except Exception as e:
        return

    if usertype == ClientConsumer.WEB_USER_TYPE:  # web用户
        if islogin and userid in g_webConsumers:  # web用户上线且在当前服务器处于登录状态
            g_webConsumers.forceOffline(userid, login_time)
    elif usertype == ClientConsumer.CAR_USER_TYPE:  # car用户
        g_webConsumers.carsLogioAttentionWeb(groupid, userid, islogin)  # car用户上下线提醒

    # debug_print("userLoginLogoutInfoCallback", item['data'])


# 以私有通道订阅用户上下线信息
g_pubsub.subscribe(userLogioChannel(), userLoginLogoutInfoCallback, private_ps="user_logio_note")
