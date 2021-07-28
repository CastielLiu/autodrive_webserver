# 客户端

def check(database, data_json):
    user_name = data_json.get("user_name", None)
    passwd = data_json.get("passwd", None)
    if user_name is None or passwd is None:
        return "错误请求"
    try:
        client = database.objects.get(name=user_name, is_active=True)
    except Exception as e:
        return "用户不存在"
    if client.passwd != passwd:
        return "密码错误"


class Client:
    def __init__(self, _id, _ws):
        self.id = _id   # 客户端id
        self.ws = _ws   # 客户端websocket
        self.name = ""  # 客户端名称



