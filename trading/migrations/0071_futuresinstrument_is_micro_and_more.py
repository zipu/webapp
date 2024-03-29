# Generated by Django 4.1.3 on 2023-01-09 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0070_alter_futurestrade_realized_profit_ticks'),
    ]

    operations = [
        migrations.AddField(
            model_name='futuresinstrument',
            name='is_micro',
            field=models.BooleanField(default=False, verbose_name='마이크로'),
        ),
        migrations.AlterField(
            model_name='futuresstrategy',
            name='type',
            field=models.CharField(choices=[('entry', '진입'), ('exit', '청산')], default='entry', max_length=10, verbose_name='진입/청산'),
        ),
    ]
