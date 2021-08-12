from django.contrib import admin
from .models import Image


# Register your models here.
# 模型管理器类 - 为后台管理界面添加便于操作的新功能
class ImageManager(admin.ModelAdmin):
    # 需要列表显示的字段
    list_display = ['id', 'name', 'src']
    # 控制list_display中的字段, 哪些可以超链接到修改页面
    list_display_links = ['name']
    # 更多方法https://docs.djangoproject.com/en/2.2/ref/contrib/admin/


# 为使管理员在admin页面操作数据表, 需要在此注册
admin.site.register(Image, ImageManager)  # 第二个为可选参数[模型管理器类]
