# 数据库模型
from django.db import models


# Create your models here.
# 自动驾驶客户端
class User(models.Model):
    id = models.CharField('用户id', max_length=20, unique=True, primary_key=True)
    username = models.CharField('用户名称', max_length=20, unique=True)
    passwd = models.CharField('用户密码', max_length=20)
    is_active = models.BooleanField('是否活跃', default=True)


class CarUser(User):
    type = models.CharField('用户类型', max_length=10, default='car', choices=(('car', 'car'),), editable=False)


class WebUser(User):
    type = models.CharField('用户类型', max_length=10, default='user', choices=(('user', 'operator'),), editable=False)



