# Generated by Django 4.1.3 on 2022-12-16 20:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0036_alter_transaction_ebest_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='futurestrade',
            name='account',
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='설명'),
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='종료날짜'),
        ),
        migrations.AddField(
            model_name='futurestrade',
            name='strategy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='trades', to='trading.futuresstrategy', verbose_name='전략'),
        ),
    ]
