# Generated by Django 4.1.3 on 2022-12-10 22:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0021_futuresinstrument_ebest_symbol_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='futuresinstrument',
            name='ebest_symbol',
        ),
    ]
