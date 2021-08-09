"""autodrive_webserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import path, include
from django.views import static
from django.conf import settings
from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    # 当django配置为非调试模式并由runserver运行时将无法处理静态文件
    # 通过此配置使其能够相应静态文件请求
    # 其中STATIC_ROOT需在setting.py中设置, 为项目所有静态文件的根目录
    # 当项目不同app之间的静态文件不在同一目录时, 需要使用python manage.py collectstatic 将其收集到根目录
    url(r'^static/(?P<path>.*)$', static.serve, {'document_root': settings.STATIC_ROOT}, name='static'),

    path('admin/', admin.site.urls),
    path('test/', views.test_html),
    url(r'^favicon\.ico$', RedirectView.as_view(url=r'static/images/favicon.ico')),  # 配置图标

    # 分布式路由
    path('bookstore/', include('apps.bookstore.urls')),
    path('autodrive/', include('apps.autodrive.urls')),

]
