# 数据库模型
from django.db import models


class UserGroup(models.Model):
    name = models.CharField('用户组名称', max_length=20, unique=True, primary_key=True)
    supergroup = models.BooleanField('超级用户组', default=False)


def default_user_group():
    return UserGroup.objects.get_or_create(name="empty")[0].name


# Create your models here.
# 自动驾驶客户端
class User(models.Model):
    userid = models.CharField('用户ID', max_length=20, unique=True, primary_key=True)
    username = models.CharField('用户名称', max_length=20, unique=True)
    password = models.CharField('用户密码', max_length=20)
    # 关联用户组, 并设置保护, 当组内用户非空时, 禁止删除
    group = models.ForeignKey(UserGroup, on_delete=models.PROTECT, default=default_user_group)

    token = models.CharField('临时令牌', max_length=50, blank=True, null=True)
    is_online = models.BooleanField('是否在线', default=False)
    is_active = models.BooleanField('是否活跃', default=True)
    CarType = "car"
    WebType = "web"


class CarUser(User):
    type = models.CharField('用户类型', max_length=10, default=User.CarType, choices=((User.CarType, User.CarType),), editable=False)


class WebUser(User):
    type = models.CharField('用户类型', max_length=10, default=User.WebType, choices=((User.WebType, User.WebType),), editable=False)
    is_super = models.BooleanField('是否超级用户', default=False)


class PathInfo(models.Model):
    # / var / lib / mysql / files / autodrive / paths
    # path = models.FilePathField
    # models.FileField
    # models.ImageField
    # models.
    pass
