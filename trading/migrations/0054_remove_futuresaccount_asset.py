# Generated by Django 4.1.3 on 2022-12-21 13:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0053_alter_futuresaccount_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='futuresaccount',
            name='asset',
        ),
    ]
