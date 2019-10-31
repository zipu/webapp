# Generated by Django 2.2.6 on 2019-10-31 05:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0004_auto_20191031_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='futuresentry',
            name='commission_krw',
            field=models.FloatField(blank=True, null=True, verbose_name='수수료(원)'),
        ),
        migrations.AlterField(
            model_name='futuresentry',
            name='cum_commission_krw',
            field=models.FloatField(blank=True, null=True, verbose_name='누적수수료(원)'),
        ),
        migrations.AlterField(
            model_name='futuresentry',
            name='timestamp',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='타임스탬프'),
        ),
        migrations.AlterField(
            model_name='futuresexit',
            name='timestamp',
            field=models.PositiveIntegerField(blank=True, max_length=32, null=True, verbose_name='타임스탬프'),
        ),
    ]
