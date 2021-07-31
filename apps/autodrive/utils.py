from django.db.models import Q, F
from random import Random
import string


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


def delteToken(database, username):
    try:
        # 使用Q对象筛选用户, 查找username或userid匹配的用户
        db_user = database.objects.get(Q(username=username) | Q(userid=username) & Q(is_active=True))
        db_user.token = None
        db_user.save()
    except Exception as e:
        return False


# 用户登录验证, 使用user_id/user_name + password进行登录验证
# @param database: 用户信息数据库
# @param user_id, user_name, password, token: 用户请求登录数据
# @return 验证结果
def userLoginCheck(database, user_id, user_name, password, token=""):
    result = {"ok": False, "info": "xx"}

    # users = database.objects.all()
    # for user in users:
    #     print(user.password, user.userid, user.username)

    try:
        # 使用Q对象筛选用户, 查找username或userid匹配的用户
        db_user = database.objects.get(Q(username=user_name) | Q(userid=user_id) & Q(is_active=True))
    except Exception as e:
        result['info'] = "用户不存在"
        return result

    if db_user.password != password and db_user.token != token:
        result['info'] = "密码或token错误"
        return result

    if token == "":  #
        db_user.token = randomToken(20)  # 登录验证成功, 生成token并存储在数据库
        db_user.save()  # 只有调用save后才会保存到数据库

    result['ok'] = True
    result['info'] = "验证成功"
    result['username'] = db_user.username
    result['userid'] = db_user.userid
    result['token'] = db_user.token
    return result



