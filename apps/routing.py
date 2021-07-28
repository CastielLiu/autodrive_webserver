# apps websocket主路由

from django.urls import path
from apps.autodrive import consumers

websocket_urlpatterns = [
    path('autodrive/test/', consumers.TestConsumer),

    # core用于客户端登录以及传输核心数据
    # 其他路由访问时需上报用户名或其他信息由服务器校验, 若未通过core注册则拒绝连接
    path('autodrive/car/core/', consumers.CarClientsConsumer),
    path('autodrive/web/core/', consumers.UserClientConsumer),

    # path('autodrive/car/video/', ) # 车端视频上报, 与core分离,避免数据拥堵

]
