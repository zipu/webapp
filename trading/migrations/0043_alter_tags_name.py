# Generated by Django 4.1.3 on 2022-12-18 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0042_remove_futurestrade_tags_futurestrade_entry_tags_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tags',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='태그'),
        ),
    ]
