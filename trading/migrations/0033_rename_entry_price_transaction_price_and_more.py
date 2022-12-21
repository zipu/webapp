# Generated by Django 4.1.3 on 2022-12-15 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0032_futurestrade_commission_futurestrade_paper_profit_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='entry_price',
            new_name='price',
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='avg_entry_price',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=12, null=True, verbose_name='평균진입가'),
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='avg_exit_price',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=12, null=True, verbose_name='평균청산가'),
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='current_price',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=12, null=True, verbose_name='현재가'),
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='num_entry_cons',
            field=models.SmallIntegerField(default=0, verbose_name='총진입계약수'),
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='num_exit_cons',
            field=models.SmallIntegerField(default=0, verbose_name='총청산계약수'),
        ),
    ]