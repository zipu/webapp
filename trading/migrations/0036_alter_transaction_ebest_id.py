# Generated by Django 4.1.3 on 2022-12-16 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0035_futuresrecord_remove_transaction_account_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='ebest_id',
            field=models.PositiveSmallIntegerField(verbose_name='이베스트 체결번호'),
        ),
    ]
