# 数据库模型
from django.db import models


# Create your models here.
class Book(models.Model):
    title = models.CharField('书名', max_length=50, default='' , unique=True)
    pub = models.CharField('出版社', max_length=50, default='')
    price = models.DecimalField('价格', max_digits=7, decimal_places=2, default=0.0)
    discount = models.DecimalField('折扣', max_digits=3, decimal_places=2, default=1.0)
    market_price = models.DecimalField('零售价', max_digits=5, decimal_places=2, default=0.0)
    is_active = models.BooleanField('是否活跃', default=True)

    # print该类时 格式化显示
    def __str__(self):
        return '%s_%s_%s_%s' % (self.title, self.price, self.market_price, self.pub)

    # 内建Meta类
    class Meta:
        # 重命名表名
        db_table = 'book'
        verbose_name = '图书'  # 用于admin后台显示的名字(单数), 否则为默认值
        verbose_name_plural = verbose_name


class Author(models.Model):
    name = models.CharField('姓名', max_length=11)
    age = models.IntegerField('年龄', default=1)
    email = models.EmailField('邮箱', null=True) # 允许为空

    class Meta:
        db_table = 'author'

