# 数据库模型
from django.db import models


# Create your models here.
# 自动驾驶客户端
class User(models.Model):
    userid = models.CharField('用户ID', max_length=20, unique=True, primary_key=True)
    username = models.CharField('用户名称', max_length=20, unique=True)
    password = models.CharField('用户密码', max_length=20)
    token = models.CharField('临时令牌', max_length=50, null=True)
    is_online = models.BooleanField('是否在线', default=False)
    is_active = models.BooleanField('是否活跃', default=True)


class CarUser(User):
    type = models.CharField('用户类型', max_length=10, default='car', choices=(('car', 'car'),), editable=False)


class WebUser(User):
    type = models.CharField('用户类型', max_length=10, default='ws_client', choices=(('ws_client', 'operator'),), editable=False)



