from . import views
from django.urls import path

urlpatterns = [
    path('', views.main_page),
    path('login/', views.login),
    path('logout/', views.logout),
    path('test/', views.test_page),

]
