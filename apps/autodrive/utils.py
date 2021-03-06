import datetime
import time
from functools import partial
from django.conf import settings
from django.db.models import Q, F, QuerySet
from random import Random
import string


# 自定义调试打印函数  def print(self, *args, sep=' ', end='\n', file=None)
from apps.autodrive.models import CarUser


def debug_print(self, *args, sep=' ', end='\n', file=None):
    if settings.DEBUG:
        print(time.time(), end=' ')
        print(self, *args, sep=sep, end=end, file=file)


# 对字典浮点数据进行精度处理
# @param obj 字典对象
# @param cnt 保留小数点位数
def pretty_floats(obj, cnt):
    if isinstance(obj, float):
        return round(obj, cnt)
    elif isinstance(obj, dict):
        return dict((k, pretty_floats(v, cnt)) for k, v in obj.items())
    elif isinstance(obj, (list, tuple)):
        # map(fun, list) 根据提供的函数对指定的序列做映射, 用fun依次处理列表数据, 然后返回一个新列表
        # partial(fun, params) 给fun绑定一个参数然后返回一个新的可调用对象
        return list(map(partial(pretty_floats, cnt=cnt), obj))
    return obj


# 随机字符串
def randomStr(str_len):
    res = ''
    chars = string.ascii_letters + string.digits
    for i in range(str_len):
        res += chars[Random().randint(0, len(chars) - 1)]
    return res


# 生成随机令牌,
# 用户使用帐号密码登录验证成功后生成, 退出后删除
# 在用户退出之前发起ws请求, 可利用用户名+token进行新验证
# 此项目中, 拟定同一用户可发起多个web连接,
# 客户端可通过http或ws: core进行帐号密码登录, 随后的ws验证使用token
# 用户退出登录之前发起新的web连接时, 利用用户名和token进行验证(如何避免用户名和token被非法获得)
def randomToken(token_len=10):
    token = ''
    chars = string.ascii_letters + string.digits
    for i in range(token_len):
        token += chars[Random().randint(0, len(chars) - 1)]
    return token


# @param login_time 登录时间, 如果与数据库中记录的时间不符, 则表明已被新登录覆盖
def userLogout(database, username, login_time=None):
    try:
        # 使用Q对象筛选用户, 查找username或userid匹配的用户
        db_user = database.objects.get(Q(username=username) | Q(userid=username) & Q(is_active=True))
        if login_time is None or login_time == db_user.login_time.strftime("%Y%m%d%H%M%S%f"):
            db_user.is_online = False
            db_user.session_key = ""
            db_user.token = None  #

        db_user.save()
    except Exception as e:
        print(e)
        return False


# 用户登录验证, 使用user_id/user_name + password/token进行登录验证
# @param database: 用户信息数据库
# @param user_id, user_name, password, token: 用户请求登录验证的数据
# @param update_db, 是否更新到数据库
# @param session_key 会话id(参数非空时将其写入到数据库, 并生成token)
# @return 验证结果
def userLoginCheck(database, user_id, user_name, password, token="", session_key=""):
    result = {"ok": False, "info": ""}

    # users = database.objects.all()
    # for user in users:
    #     print(user.userid, user.username, user.password)
    # print("%s_%s_%s" % (user_id, user_name, password))
    try:
        # 使用Q对象筛选用户, 查找username或userid匹配的用户
        db_user = database.objects.get((Q(username=user_name) | Q(userid=user_id)) & Q(is_active=True))
    except Exception as e:
        print(e)
        result['info'] = "No user!"
        return result

    if db_user.password != password and db_user.token != token:
        result['info'] = "Error password or token"
        return result

    # 用户已在线且处于操作锁定状态, 禁止其他用户登录
    if db_user.is_online and db_user.op_lock:
        result['ok'] = False
        result['info'] = ""
        return result

    if session_key:  # session_key 非空, 表明为新会话, 保存并生成token, 用于用户登录验证ws
        db_user.session_key = session_key
        db_user.token = randomToken(20)  # 登录验证成功, 生成token并存储在数据库
    else:
        db_user.is_online = True
        db_user.login_time = datetime.datetime.now()  # 记录登录时间
        result['logintime'] = db_user.login_time.strftime("%Y%m%d%H%M%S%f")
        debug_print("%s logged in in %s" % (db_user.username, db_user.login_time))
    db_user.save()  # 只有调用save后才会保存到数据库

    result['ok'] = True
    result['info'] = "Successed login"
    result['username'] = db_user.username
    result['userid'] = db_user.userid
    result['token'] = db_user.token
    result['group'] = db_user.group.name
    result['groupid'] = db_user.group.id
    result['usertype'] = db_user.type

    if db_user.type == db_user.WebType:
        result['is_super'] = db_user.is_super
    return result


# @brief 查询某用户的部分数据
# @param db 数据库
# @param userid 用户id
# @return values_list tuple
def queryValuesListByUserId(db, userid, *args):
    try:
        return db.objects.values_list(*args).get(userid=userid)  # tuple
        # return db.objects.values_list(args).get(userid=userid)  # dict
    except Exception as e:
        print(e)
        return None


# @brief 查询组内所有车辆
# @param groupid 用户组
# @return ["carid", ...]
def queryCarsInGroup(groupid):
    try:
        res = []
        cars = CarUser.objects.filter(group__id=groupid)
        for car in cars:
            res.append(car.userid)
        return res
    except Exception as e:
        return []


# @brief 将http请求转发经websocket转发到车端
# @param clients 车辆用户列表
# @param car_id 车辆ID
# @param sync 是否同步
# @return res是否成功, 错误消息/响应内容
def transmitFromHttpToWebsocket(clients, car_id, content, sync=True):
    car_client = clients.get(car_id)
    if car_client is None:
        return False, "Car offline"

    request_task = car_client.reqest_task
    request_task.cv.acquire()
    try:
        car_client.ws.send(bytes_data=content)  # 将http请求指令经ws转发到车端
    except Exception as e:
        debug_print("ws req_task err: ", e)
        return False, "Car communication error"

    if request_task.cv.wait(10.0):  # 等待10s
        response_text = request_task.response
    else:
        return False, "Request timeout in server"
    request_task.cv.release()
    return True, response_text
