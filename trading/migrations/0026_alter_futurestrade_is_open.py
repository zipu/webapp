# Generated by Django 4.1.3 on 2022-12-12 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0025_futurestrade_is_open'),
    ]

    operations = [
        migrations.AlterField(
            model_name='futurestrade',
            name='is_open',
            field=models.BooleanField(verbose_name='상태'),
        ),
    ]
