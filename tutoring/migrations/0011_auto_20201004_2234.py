# Generated by Django 3.0.3 on 2020-10-04 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0010_auto_20201004_2208'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='homework',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='숙제'),
        ),
        migrations.AlterField(
            model_name='attendence',
            name='homework',
            field=models.SmallIntegerField(choices=[(1, '잘해옴'), (2, '부족'), (3, '안함')], verbose_name='숙제'),
        ),
        migrations.AlterField(
            model_name='tuition',
            name='payment',
            field=models.CharField(choices=[('wechat', '위챗페이'), ('alipay', '즈푸바오'), ('cash', '현금')], max_length=250),
        ),
    ]
