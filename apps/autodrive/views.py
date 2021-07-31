from functools import wraps

from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from apps.autodrive.consumers import g_car_clients, g_user_clients
import json
from apps.autodrive.utils import userLoginCheck, randomToken, delteToken
from apps.autodrive.models import WebUser


# Create your views here.
# 说明：这个装饰器的作用，就是在每个视图函数被调用时，都验证下有没有登录
# 如果有过登录，则可以执行新的视图函数，
# 否则没有登录则自动跳转到登录页面。
def check_login(f):
    # wraps装饰器, 避免获取装饰函数的名字和注释时获取到装饰器内嵌函数的名字和注释
    # 名字f.__name__ 注释f.__doc__
    @wraps(f)
    def inner(request, *arg, **kwargs):
        if request.session.get('is_login', False):
            return f(request, *arg, **kwargs)
        else:
            return redirect('/autodrive/login/')
    return inner


# 进入视图函数之前, request经过了中间件处理, 当请求中的cookie包含SESSION_COOKIE_NAME时,
# session中间件(如果启用了)将从数据库或其他途径(用户配置)获取保存的session信息
# request.session将被系统保存, 下次请求时利用SESSION_COOKIE_NAME查找出来
# request.session保存规则有2种: SESSION_SAVE_EVERY_REQUEST true: 每次都保存/false: 修改后保存
def login(request):
    # print("COOKIES['sessionid']", request.COOKIES.get('sessionid'))
    # print("is_login", request.session.get('is_login', 0))

    # 如果是GET请求，就说明是用户刚开始登录，使用URL直接进入登录页面的
    if request.method != "POST":
        # 已登录，将页面从定向到主页
        if request.session.get('is_login', False):
            return redirect("/autodrive/")
        return render(request, 'autodrive/login.html')

    user_name = request.POST.get('username')
    password = request.POST.get('password')
    login_res = userLoginCheck(WebUser, user_name, user_name, password)

    if login_res['ok']:  # 登录成功 ,标记 is_login
        request.session['is_login'] = True
        request.session['username'] = login_res['username']
        request.session['password'] = password
        respose = redirect(request.GET.get('next'))
        respose.set_cookie('token', login_res['token'])
        respose.set_cookie('test', 'test')
        return respose
    else:
        return render(request, 'autodrive/login.html')


def logout(request):
    # 从会话中清除登录状态
    # request.session['is_login'] = False

    print(request.session.get('username'))
    delteToken(WebUser, request.session.get('username'))
    request.session.clear()  # 清空会话数据
    # 从定向到登录页面
    return redirect("/autodrive/login")


@check_login
def main_page(request):
    if request.method == "GET":
        username = request.session.get("username", "")
        password = request.session.get("password", "")
        return render(request, 'autodrive/index.html', locals())
    elif request.method != "POST":
        return HttpResponseNotFound()

    response = {"type": "未知", "msg": "错误请求"}
    reqest_body = json.loads(request.body)
    msg_type = reqest_body.get("type")
    msg = reqest_body.get("msg")

    if msg_type == "req_online_car":  # 请求获取在线车辆列表
        cars = []
        for car_id, car_client in g_car_clients.items():
            cars.append({"id": car_id, "name": car_client.name})

        response["type"] = "res_online_car"
        response["msg"] = {"cars": cars}
        # "msg": {"cars": [{"id": x, "name": x}]}

    return HttpResponse(json.dumps(response))


def test_page(request):
    return render(request, 'autodrive/test.html')
