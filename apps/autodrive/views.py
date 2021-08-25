from functools import wraps

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, FileResponse, HttpResponseNotFound
from django.views import static
from django.views.decorators.csrf import csrf_exempt
from django.contrib.staticfiles.views import serve

from apps.autodrive.consumers import g_car_clients, g_user_clients
import json
from apps.autodrive.utils import userLoginCheck, debug_print, userLogout, pretty_floats, getValuesListByUserId
from apps.autodrive.models import WebUser, CarUser, User, NavPathInfo
from apps.autodrive.nodes.nav_path import *
import zipfile


# 返回渲染登录页面
def render_login_page(request, _locals={}, *args):
    # 此处务必对session进行修改, 迫使session中间件生成seesion_id(如果不存在)
    # 如此, 客户端登录成功时才能正确获取session_id并保存
    request.session['is_login'] = False

    # 针对能够重定向的请求，render一个页面
    response = render(request, 'autodrive/login.html', _locals, args)

    # 针对不支持重定向的AJAX请求，返回一个URL，由其自行请求新页面
    response['REDIRECT'] = request.build_absolute_uri() + "login/"
    return response


# 判断会话是否异常
def session_err(request):
    # 获取指定用户名以及会话id的用户, 若用户数为0, 则表明会话已经失效
    users = User.objects.filter(Q(session_key=request.session.session_key) &
                                Q(userid=request.session.get('userid')))
    if users.count() == 0:
        request.session.clear()
        # print(users.count(), request.session.session_key)
        return True
    return False


# Create your views here.
# 说明：这个装饰器的作用，就是在每个视图函数被调用时，都验证下有没有登录
# 如果有过登录，则可以执行新的视图函数，
# 否则没有登录则自动跳转到登录页面。
def check_login(f):
    # wraps装饰器, 避免获取装饰函数的名字和注释时获取到装饰器内嵌函数的名字和注释
    # 名字f.__name__ 注释f.__doc__
    @wraps(f)
    def inner(request, *arg, **kwargs):
        if request.session.get('is_login', False) and not session_err(request):
            return f(request, *arg, **kwargs)
        else:
            usertype = request.session.get('usertype', User.WebType)
            if usertype == User.WebType:
                return render_login_page(request)
            else:
                return HttpResponse("please login first")

    return inner


# 进入视图函数之前, request经过了中间件处理, 当请求中的cookie包含SESSION_COOKIE_NAME时,
# session中间件(如果启用了)将从数据库或其他途径(用户配置)获取保存的session信息
# request.session将被系统保存, 下次请求时利用SESSION_COOKIE_NAME查找出来
# request.session保存规则有2种: SESSION_SAVE_EVERY_REQUEST true: 每次都保存/false: 修改后保存
def login_page(request):
    # 如果是GET请求，就说明是用户刚开始登录，使用URL直接进入登录页面的
    if request.method == "GET":
        # 会话状态已登录，将页面从定向到主页
        if request.session.get('is_login', False):
            return redirect("/autodrive/")
        else:  # 会话状态未登录, render登录页面
            return render_login_page(request)

    # 确保客户端通过get login页面获得了session_id
    # if request.session.get('is_login') is None:
    if request.session.session_key is None:
        # 会话尚未建立, 客户端却发送了POST请求, render到登录页面
        return render_login_page(request)

    # 用户登录成功后将session_key写入数据库覆盖旧值,
    # 当用户在另一设备登录时，未退出的帐号session_key失效而被迫退出
    # cookies中的settings.SESSION_COOKIE_NAME可能被session中间件使用后删除了,
    # 因此使用request.session.session_key代替request.COOKIES.get(settings.SESSION_COOKIE_NAME, "")
    session_key = request.session.session_key
    username = request.POST.get('username')
    password = request.POST.get('password')
    usertype = request.POST.get('usertype', User.WebType)

    if usertype == User.WebType:
        login_res = userLoginCheck(WebUser, username, username, password, session_key=session_key)
    elif usertype == User.CarType:
        login_res = userLoginCheck(CarUser, username, username, password, session_key=session_key)
    else:
        return HttpResponse("Error user type")

    if login_res['ok']:  # 登录成功 ,标记 is_login
        # print("登录成功", login_res)
        request.session['is_login'] = True
        request.session['usertype'] = usertype
        request.session.update(login_res)  # 合并字典,取代逐个复制

        if usertype == User.WebType:
            respose = redirect(request.GET.get('next'))
        else:
            data = {"type": "res_login", "code": 0, "msg": login_res['info']}
            respose = HttpResponse(json.dumps(data))

        # 原方案在此处向cookie中添加userid和token, 但由于部分请求在上面已经退出, 无法获得新cookie
        # 于是将userid和token的发放写在了main_page, 以使被重定向的客户也能得到信息

        return respose
    else:
        if usertype == User.WebType:
            error = login_res['info']
            return render_login_page(request, locals())
            # return render(request, 'autodrive/login.html', locals())
        else:
            data = {"type": "res_login", "code": 1, "msg": login_res['info']}
            return HttpResponse(json.dumps(data))


@check_login
def logout_page(request):
    # 从会话中清除登录状态
    # request.session['is_login'] = False

    debug_print(request.session.get('username'), "logout")
    userLogout(WebUser, request.session.get('username'))
    request.session.clear()  # 清空会话数据

    # 从定向到登录页面
    return render_login_page(request)


@check_login
def main_page(request):
    username = request.session.get("username", "")
    usergroup = request.session.get("group", "默认组")  # 用户组
    is_super = request.session.get("is_super", False)  # 超级用户

    # print("所属组：", usergroup, "是否为超级用户:", is_super)

    if request.method == "GET":
        userid = request.session.get("userid")
        token = request.session.get("token")
        if userid is None or token is None:  # 会话中缺少关键字段信息
            return render_login_page(request)

        response = render(request, 'autodrive/index.html', locals())
        # 将token与userid经cookie发送给用户, 用户登录验证websocket
        # 最初方案为保存userame但测试表明cookie设置中文出现问题, 从而修改为保存id
        response.set_cookie('userid', userid)
        response.set_cookie('token', token)
        return response
    debug_print("%s" % str(request.body))

    reqest_body = json.loads(request.body)
    req_type = reqest_body.get("type", "")
    data = reqest_body.get("data", {})

    # code默认0为成功, 其他根据type进行编码
    response = {"type": "", "code": 0, "msg": "", "data": {}}
    response_text = ""

    if req_type == "req_online_car":  # 请求获取(组内)在线车辆列表
        response['type'] = 'res_online_car'
        car_group = data.get('group', '')  # 期望获取的车辆组

        # 如果请求组名非字符串或为空串, 默认请求用户组
        if not isinstance(car_group, str) or car_group == "":
            car_group = usergroup

        if usergroup != car_group and not is_super:  # 非超级用户且非组内用户
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
    elif req_type == "req_path_list":  # 请求获取路径列表
        response['type'] = 'res_path_list'
        path_group = data.get('group', usergroup)  # 期望获取的路径组, 如果没有该参数, 则默认获取当前用户组
        path_list = getAvailbalePaths(path_group)
        if path_list is None:
            response['code'] = 1
        else:
            response['data'] = {"path_list": path_list}
        response_text = json.dumps(response, ensure_ascii=False)  # ensure_ascii=False 允许中文编码
    elif req_type == "req_path_traj":  # 获取路径轨迹
        response['type'] = 'res_path_traj'
        pathid = data.get('pathid', -1)

        ok, msg, path = getNavPathTraj(usergroup, pathid)
        if not ok:
            response['code'] = 1
            response['msg'] = msg
        else:
            response['data'] = {"path": path}
        # json.encoder.FLOAT_REPR = lambda x: format(x, '.2f')  #json为浮点数保留一定位数, 当优化器存在时无效
        # print(pretty_floats(response, 5))
        response_text = json.dumps(pretty_floats(response, 5), ensure_ascii=False)
    elif req_type == "req_path_files":  # 获取路径文件(返回文件urls)
        response['type'] = 'res_path_files'
        pathid = data.get('pathid', -1)
        if pathid == -1:
            response['code'] = 9  # 格式错误
            response['msg'] = "format error"
        else:
            navpaths = NavPathInfo.objects.filter(Q(id=pathid) & Q(uploader__group__name=usergroup))
            if navpaths.count() != 1:
                response['code'] = 1
                response['msg'] = "No path"
            else:
                navpath = navpaths[0]
                path_urls = navpath.pathfile_urls()  # 获取路径文件下载url
                if len(path_urls) == 0:
                    response['code'] = 2
                    response['msg'] = "No path files"
                else:
                    response['code'] = 0
                    response['data'] = {"path_urls": path_urls, "path_name": navpath.name}
        response_text = json.dumps(response)
    elif req_type == "req_cars_pos":
        response['type'] = 'res_cars_pos'
        cars_pos = []
        carsid = data.get('cars_id', [])
        for carid in carsid:
            # carObjs = CarUser.objects.filter(userid=carid)
            _data = getValuesListByUserId(CarUser, carid, "latitude", "longitude", "is_online")
            if _data:
                cars_pos.append({'car_id': carid, 'lat': _data[0], 'lng': _data[1],
                                 'online': _data[2]})

        cars_pos.append({'car_id': 'test_car', 'lat': 33.37287, 'lng': 120.15607,
                         'online': False})

        if len(cars_pos):
            response['code'] = 0
        else:
            response['code'] = 1
        response['data'] = {'cars_pos': cars_pos}
        response_text = json.dumps(response)
    else:
        response['code'] = 1
        response['msg'] = "Unknown request."
        response_text = json.dumps(response)
    debug_print(response_text)
    return HttpResponse(response_text)


def test_page(request):
    return render(request, 'autodrive/test.html')


# 自定义上传文件服务视图函数(调用内置静态文件服务), 以确保访问权限
@check_login
def uploaded_serve(request, path, document_root=None, show_indexes=False):
    return static.serve(request, path, document_root, show_indexes)
