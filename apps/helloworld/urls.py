from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/all_book
    path('test/', views.test_html),
    path('a_upload/', views.a_upload)
]