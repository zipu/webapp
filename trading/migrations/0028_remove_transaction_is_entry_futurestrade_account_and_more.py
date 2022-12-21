# Generated by Django 4.1.3 on 2022-12-12 18:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0027_alter_transaction_is_entry'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='is_entry',
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trades', to='trading.futuresaccount', verbose_name='계좌'),
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='position',
            field=models.SmallIntegerField(blank=True, choices=[(1, 'Long'), (-1, 'Short')], null=True, verbose_name='포지션'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='trading.futuresaccount', verbose_name='계좌'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='trade',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='trading.futurestrade', verbose_name='거래'),
        ),
        migrations.AlterField(
            model_name='futurestrade',
            name='is_open',
            field=models.BooleanField(default=True, verbose_name='상태'),
        ),
    ]