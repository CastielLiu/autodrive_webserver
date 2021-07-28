# apps websocket主路由

from django.urls import path
from apps.autodrive import consumers

websocket_urlpatterns = [
    path('autodrive/test/', consumers.TestConsumer),
    path('autodrive/car/core/', consumers.CarClientsConsumer),
    path('autodrive/user/core/', consumers.UserClientConsumer),

]
