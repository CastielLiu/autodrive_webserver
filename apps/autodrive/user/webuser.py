# 远程用户客户端
# 当前开发针对web端客户

from .user import Client


# 用户控制指令
class UserCtrl:
    def __init__(self):
        self.speed = None
        self.steer_angle = None


# 用户客户端
class UserClient(Client):
    def __init__(self, user_id, ws):
        Client.__init__(self, user_id, ws)
        self.ctrl_cmd = UserCtrl()
