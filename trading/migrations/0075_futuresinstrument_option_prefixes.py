# Generated by Django 4.1.3 on 2023-06-16 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0074_futuresinstrument_option_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='futuresinstrument',
            name='option_prefixes',
            field=models.CharField(default='', max_length=100, verbose_name='옵션명'),
        ),
    ]
