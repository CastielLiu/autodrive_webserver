from . import views
from django.urls import path

urlpatterns = [
    path('', views.main_page),
    path('test/', views.test_page),

]
