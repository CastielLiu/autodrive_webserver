from functools import wraps

from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from apps.autodrive.consumers import g_car_clients, g_user_clients
import json
from apps.autodrive.utils import userLoginCheck, randomToken, userLogout, pretty_floats
from apps.autodrive.models import WebUser, CarUser
from apps.autodrive.nodes.nav_path import *


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

        print("登录成功", login_res)
        request.session['is_login'] = True
        request.session.update(login_res)  # 合并字典,取代逐个复制

        # request.session['username'] = login_res['username']
        # request.session['userid'] = login_res['userid']
        # request.session['password'] = password
        # request.session['group'] = login_res['group']
        # request.session['is_super'] = login_res['is_super']

        respose = redirect(request.GET.get('next'))

        # 将token与userid经cookie发送给用户, 用户登录验证websocket
        # 最初方案为保存userame但测试表明cookie设置中文出现问题, 从而修改为保存id
        respose.set_cookie('userid', login_res['userid'])
        respose.set_cookie('token', login_res['token'])

        print(respose.cookies)
        return respose
    else:
        error = login_res['info']
        return render(request, 'autodrive/login.html', locals())


@check_login
def logout(request):
    # 从会话中清除登录状态
    # request.session['is_login'] = False

    print(request.session.get('username'), "logout")
    userLogout(WebUser, request.session.get('username'))
    request.session.clear()  # 清空会话数据

    # 从定向到登录页面
    return redirect("/autodrive/login")


@check_login
def main_page(request):
    username = request.session.get("username", "")
    userid = request.session.get("userid", "")
    group = request.session.get("group", "默认组")  # 用户组
    is_super = request.session.get("is_super", False)  # 超级用户

    print("所属组：", group, "是否为超级用户:", is_super)

    if request.method == "GET":
        # username = request.session.get("username", "")
        # password = request.session.get("password", "")
        return render(request, 'autodrive/index.html', locals())
    elif request.method != "POST":
        return HttpResponseNotFound()

    reqest_body = json.loads(request.body)
    req_type = reqest_body.get("type", "")
    data = reqest_body.get("data", {})
    print("autodrive post req_type: ", req_type)

    # code默认0为成功, 其他根据type进行编码
    response = {"type": "", "code": 0, "msg": "", "data": {}}
    response_text = json.dumps({"type": "", "code": 1, "msg": "", "data": {}})
    if req_type == "req_online_car":  # 请求获取在线车辆列表
        response['type'] = 'res_online_car'
        car_group = data.get('group', '')

        if group != car_group and not is_super:
            response['code'] = 7  # 非组内用户(无权限)
        else:
            cars = []
            try:
                if is_super:
                    db_cars = CarUser.objects.filter(is_active=True)  # 超级权限, 显示所有用户
                else:
                    db_cars = CarUser.objects.filter(group=car_group, is_active=True)
                for db_car in db_cars:
                    # print("%s, %s, %s" % (db_car.group.supergroup, db_car.group.name, group))
                    cars.append({"id": db_car.userid, "name": db_car.username, "group": db_car.group.name,
                                 "online": db_car.is_online})
            except Exception as e:
                pass

            # 在线车辆
            # for car_id, car_client in g_car_clients.items():
            #     cars.append({"id": car_id, "name": car_client.name})

            response["data"] = {"cars": cars}
            response_text = json.dumps(response)
            # "data": {"cars": [{"id": x, "name": x}]}
    elif req_type == "req_path_list":  # 获取路径列表
        response['type'] = 'res_path_list'
        path_list = getAvailbalePaths(group)
        if path_list is None:
            response['code'] = 1
        else:
            response['data'] = {"path_list": path_list}
        response_text = json.dumps(response, ensure_ascii=False)  # ensure_ascii=False 允许中文编码

    elif req_type == "req_path": # 获取路径信息
        response['type'] = 'res_path'
        pathid = data.get('pathid', -1)

        path = getNavPath(pathid)
        if path is None:
            response['code'] = 1
        else:
            response['data'] = {"path": path}
        # json.encoder.FLOAT_REPR = lambda x: format(x, '.2f')  #json为浮点数保留一定位数, 当优化器存在时无效
        # print(pretty_floats(response, 5))
        response_text = json.dumps(pretty_floats(response, 5), ensure_ascii=False)

    return HttpResponse(response_text)


def test_page(request):
    return render(request, 'autodrive/test.html')
