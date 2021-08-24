# 数据库模型
from django.db import models
from .customize_fields import RestrictedFileField
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver


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
    session_key = models.CharField('会话ID', max_length=40, blank=True, default="")
    token = models.CharField('临时令牌', max_length=50, blank=True, null=True)
    is_online = models.BooleanField('是否在线', default=False)
    is_active = models.BooleanField('是否活跃', default=True)
    CarType = "car"
    WebType = "web"


class CarUser(User):
    type = models.CharField('用户类型', max_length=10, default=User.CarType, choices=((User.CarType, User.CarType),), editable=False)
    longitude = models.FloatField('经度', default=0.0)
    latitude = models.FloatField('纬度', default=0.0)
    soc = models.IntegerField('剩余电量', default=-1)


class WebUser(User):
    type = models.CharField('用户类型', max_length=10, default=User.WebType, choices=((User.WebType, User.WebType),), editable=False)
    is_super = models.BooleanField('是否超级用户', default=False)


# 导航路径信息模型
class NavPathInfo(models.Model):
    # 动态生成文件路径
    # @param instance 当前模型实例
    # @param filename 上传时的文件名
    def file_path(self, filename):
        return '%s/%s/%s/%s' % ('autodrive_paths', self.uploader.group.name, self.name, filename)

    # 关联上传者, 删除时不设保护
    uploader = models.ForeignKey(WebUser, models.DO_NOTHING, blank=False, null=True, verbose_name="上传者")

    # auto_now_add=True 自动添加上传时间, 不可修改
    # auto_now=True 自动保存每次save的时间
    upload_time = models.DateTimeField('上传时间', auto_now_add=True)

    # 当storage参数为空时, 模型将上传的文件存储到settings.MEDIA_ROOT路径
    # storage可以设置为数据库存储, 目前笔者尚未找到合适方案
    points_file = RestrictedFileField(upload_to=file_path, verbose_name="路径点文件", null=True, blank=False,
                                      max_upload_size=5242880, content_types=['text/plain'])
    extend_file = RestrictedFileField(upload_to=file_path, verbose_name="路径拓展文件", null=True, blank=True,
                                      max_upload_size=2621440, content_types=['text/xml'])
    # 路径名称中不允许包含特殊字符, 不允许重复
    name = models.CharField('路径名称', max_length=30, null=True, blank=False, unique=True)
    is_active = models.BooleanField('是否活跃', default=True)  # 请求删除时标记为False, 便于删除后找回

    # 内建Meta类
    class Meta:
        # db_table = 'navpathinfo'  # 重命名数据库表名, 默认按照系统规则命名
        verbose_name = '导航路径'  # 用于admin后台显示的名字(单数), 否则为默认值
        verbose_name_plural = verbose_name

    def pathfile_urls(self):
        urls = []
        if self.points_file.name:
            # self.points_file.storage.base_url MEDIA_URL
            # self.points_file.storage.base_location 文件存储根目录 MediaRoot/
            # self.points_file.storage.location 文件存储根目录 MediaRoot
            urls.append(self.points_file.storage.base_url+self.points_file.name)
        if self.extend_file.name:
            urls.append(self.points_file.storage.base_url + self.extend_file.name)
        return urls


# 数据库类目删除时,内部文件并未删除, 利用信号事件删除文件
@receiver(pre_delete, sender=NavPathInfo)
def mymodel_delete(sender, instance, **kwargs):
    instance.points_file.delete(False)  # False不保存实例
    instance.extend_file.delete(False)
    # 下面还可添加自定义删除指令, 如文件删除后目录如果为空，目录自动删除
