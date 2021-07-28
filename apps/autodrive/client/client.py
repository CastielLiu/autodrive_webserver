# 客户端
from django.db.models import Q, F


# 用户登录, 使用user_id/user_name + password进行登录验证
# database: 用户数据库
# data_json: 用户请求登录数据
def login(database, data_json):
    user_id = data_json.get("user_id", None)
    user_name = data_json.get("user_name", None)
    password = data_json.get("password", None)

    # 登录信息不完全
    if (user_name is None and user_id is None) or password is None:
        return False, "错误请求", None

    users = database.objects.all()
    for user in users:
        print(user.password, user.userid, user.username)

    try:
        # 使用Q对象筛选用户, 查找username或userid匹配的用户
        user = database.objects.get(Q(username=user_name) | Q(userid=user_id) & Q(is_active=True))
    except Exception as e:
        return False, "用户不存在", None

    if user.password != password:
        return False, "密码错误", None
    return True, "登录成功", user.userid


class Client:
    def __init__(self, _id, _ws):
        self.id = _id  # 客户端id
        self.ws = _ws  # 客户端websocket
        self.name = ""  # 客户端名称
