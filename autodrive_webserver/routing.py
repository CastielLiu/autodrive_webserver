from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import apps.routing

# application = ProtocolTypeRouter({
#     'websocket': AuthMiddlewareStack(
#         URLRouter(
#             autodrive.routing.websocket_urlpatterns
#         )
#     ),
# })

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(apps.routing.websocket_urlpatterns)
    ),
})
