from django.contrib import admin
from .models import Book, Author
# Register your models here.


# 模型管理器类 - 为后台管理界面添加便于操作的新功能
class BookManager(admin.ModelAdmin):
    # 需要列表显示的字段
    list_display = ['id', 'title', 'pub', 'price', 'market_price']
    # 控制list_display中的字段, 哪些可以超链接到修改页面
    list_display_links = ['title']
    # 添加过滤器
    list_filter = ['pub']
    # 模糊搜索
    search_fields = ['title', 'pub']
    # 添加可在列表页编辑的字段
    list_editable = ['market_price']
    # 更多方法https://docs.djangoproject.com/en/2.2/ref/contrib/admin/


# 为使管理员在admin页面操作数据表, 需要在此注册
admin.site.register(Book, BookManager)  # 第二个为可选参数[模型管理器类]
