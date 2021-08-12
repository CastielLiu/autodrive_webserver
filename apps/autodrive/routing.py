# apps websocket主路由

from django.urls import path
from . import consumers

websocket_urlpatterns = [

    # websocket路由全部由ws开头, 以确保nginx能够将其分配给asgi服务器

    # core用于客户端登录以及传输核心数据
    # 其他路由访问时需上报用户名或其他信息由服务器校验, 若未通过core注册则拒绝连接
    # 利用不同的路由以区分web用户以及车端用户
    path('ws/autodrive/car/core/', consumers.CarClientsConsumer),
    path('ws/autodrive/web/core/', consumers.UserClientConsumer),
    # path('autodrive/car/video/', ) # 车端视频上报, 与core分离,避免数据拥堵

]
