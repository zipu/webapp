# Generated by Django 4.1.3 on 2022-12-19 23:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0047_rename_currency2_futuresinstrument_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='futurestrade',
            name='commission_krw',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=6, verbose_name='수수료(원)'),
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='realized_profit_krw',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='실현손익(원)'),
        ),
        migrations.AlterField(
            model_name='futurestrade',
            name='commission',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=6, verbose_name='수수료'),
        ),
        migrations.AlterField(
            model_name='futurestrade',
            name='duration',
            field=models.IntegerField(blank=True, null=True, verbose_name='보유기간(초)'),
        ),
    ]
