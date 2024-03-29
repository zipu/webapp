# Generated by Django 4.1.1 on 2022-10-24 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0018_alter_transfer_acc_from_alter_transfer_acc_to'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transfer',
            name='acc_from',
            field=models.CharField(choices=[('N', '없음'), ('C', '현금'), ('S', '주식'), ('FM01', '선물(해선추세)'), ('FM02', '선물(해선단타)')], max_length=10, verbose_name='출금계좌'),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='acc_to',
            field=models.CharField(choices=[('N', '없음'), ('C', '현금'), ('S', '주식'), ('FM01', '선물(해선추세)'), ('FM02', '선물(해선단타)')], max_length=10, verbose_name='입금계좌'),
        ),
    ]
