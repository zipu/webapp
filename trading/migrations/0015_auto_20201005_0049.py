# Generated by Django 3.0.3 on 2020-10-05 00:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0014_auto_20200316_2056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transfer',
            name='acc_from',
            field=models.CharField(choices=[('N', '없음'), ('C', '현금'), ('S', '주식'), ('FM', '선물(자유)'), ('FM-S', '선물(단타)')], max_length=10, verbose_name='출금계좌'),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='acc_to',
            field=models.CharField(choices=[('N', '없음'), ('C', '현금'), ('S', '주식'), ('FM', '선물(자유)'), ('FM-S', '선물(단타)')], max_length=10, verbose_name='입금계좌'),
        ),
    ]
