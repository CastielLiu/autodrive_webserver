# 客户端
from django.db.models import Q, F
from random import Random
import string


# 生成随机令牌, 用户登录验证成功后生成, 其退出之前再发起新的web请求, 可携带此token以通过新验证
# 此项目中, 拟定同一用户可发起多个web连接, 首先经core进行登录验证,验证成功后系统生成token并发放给用户
# 用户退出登录之前发起新的web连接时, 利用用户名和token进行验证(如何避免用户名和token被非法获得)
def randomToken(token_len=10):
    token = ''
    chars = string.ascii_letters + string.digits
    for i in range(token_len):
        token += chars[Random().randint(0, len(chars) - 1)]
    return token


class Client:
    def __init__(self, _type, _id, _name, _ws):
        self.type = _type  # 客户端用户类型
        self.id = _id  # 客户端用户id
        self.ws = _ws  # 客户端websocket
        self.name = _name  # 客户端用户名称
        self.token = randomToken()
