# 远程用户客户端
# 当前开发针对web端客户

from .client import Client


# 用户控制指令
class UserCtrl:
    def __init__(self):
        self.speed = None
        self.steer_angle = None


# 用户客户端
class UserClient(Client):
    def __init__(self, user_id, user_name, ws):
        Client.__init__(self, "web", user_id, user_name, ws)
        self.ctrl_cmd = UserCtrl()
