# Generated by Django 4.1.3 on 2022-12-21 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0052_rename_pricnipal_usd_futuresaccount_principal_usd'),
    ]

    operations = [
        migrations.AlterField(
            model_name='futuresaccount',
            name='date',
            field=models.DateTimeField(auto_now=True, verbose_name='날짜'),
        ),
    ]
