# Generated by Django 2.2.12 on 2021-08-24 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autodrive', '0009_auto_20210824_2341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caruser',
            name='latitude',
            field=models.FloatField(default=0.0, verbose_name='纬度'),
        ),
        migrations.AlterField(
            model_name='caruser',
            name='longitude',
            field=models.FloatField(default=0.0, verbose_name='经度'),
        ),
    ]