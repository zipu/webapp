# Generated by Django 4.1.3 on 2025-04-12 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0085_transaction_account_transaction_device'),
    ]

    operations = [
        migrations.AddField(
            model_name='futurestrade',
            name='account',
            field=models.CharField(default='A001', max_length=100, verbose_name='계좌번호'),
        ),
    ]
