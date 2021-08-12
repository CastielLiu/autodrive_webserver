from django.db import models

# Create your models here.


# 动态生成文件路径
# @param instance 当前模型实例
# @param filename 上传时的文件名
def get_file_path(instance, filename):
    return '%s/%s' % (instance.user, filename)


class Image(models.Model):
    user = models.CharField('用户名', max_length=20, null=True, blank=False)
    src = models.FileField(upload_to=get_file_path, verbose_name="用户头像", null=True, blank=False)
    name = models.CharField('图片名称', max_length=30, null=True, blank=False)
