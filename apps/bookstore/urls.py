from django.urls import path
from . import views

urlpatterns = [

    # 127.0.0.1:8000/all_book
    path('all_book/', views.all_books),

    # path转换器
    path('update_book/<int:book_id>', views.update_book),
    path('delete_book/', views.delete_book),
    path('add_book/', views.add_book)
]