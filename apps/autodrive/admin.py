from django.contrib import admin
from .models import User, CarUser, WebUser, UserGroup


# Register your models here.
# 模型管理器类 - 为后台管理界面添加便于操作的新功能
class UserManager(admin.ModelAdmin):
    # 需要列表显示的字段
    list_display = ['is_active', 'userid', 'username', 'group', 'password', 'type', 'is_online', 'token']
    # 控制list_display中的字段, 哪些可以超链接到修改页面
    list_display_links = ['userid']
    # 添加过滤器
    list_filter = ['group']
    # 模糊搜索
    search_fields = ['userid', 'username']
    # 添加可在列表页编辑的字段
    list_editable = ['group']
    # 更多方法https://docs.djangoproject.com/en/2.2/ref/contrib/admin/


# 为使管理员在admin页面操作数据表, 需要在此注册
admin.site.register(CarUser, UserManager)  # 第二个为可选参数[模型管理器类]
admin.site.register(WebUser, UserManager)


class UserGroupMaager(admin.ModelAdmin):
    list_display = ['name', 'supergroup']


# 注册
admin.site.register(UserGroup, UserGroupMaager)
