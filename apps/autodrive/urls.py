from django.conf import settings
from django.views import static

from . import views
from django.urls import path, re_path

urlpatterns = [
    path('', views.main_page),
    path('login/', views.login_page),
    path('logout/', views.logout_page),
    path('test/', views.test_page),

    path('new/login/', views.new_login),


    # re_path(r'^upload/(?P<path>.*)$', static.serve, {'document_root': settings.MEDIA_ROOT}, name='static'),
    # 使用自定义serve方法代替django内置方法(django.views.static.serve), 以添加访问权限
    # 由于这里是子路由, document_root需要
    re_path(r'^upload/(?P<path>.*)$', views.uploaded_serve, {'document_root': settings.MEDIA_ROOT}, name='static'),

]
