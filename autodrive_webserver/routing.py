from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from . import consumers
import apps.autodrive.routing

# routing与urls不同, urls支持分布路由, routing不支持
# 为实现每个应用拥有自己的routing文件, 此处采用将其路由拼接在一起进行配置
# 主应用urlpatterns
websocket_urlpatterns = [
    path('ws/autodrive/test/', consumers.TestConsumer),
]
# 子应用urlpatterns
websocket_urlpatterns += apps.autodrive.routing.websocket_urlpatterns


# 配置协议路由,
# http协议中使用的urls.urlpatterns 由django自动配置调用
# 但websocket需要自行配置
application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)  # 路由配置
    ),
})
