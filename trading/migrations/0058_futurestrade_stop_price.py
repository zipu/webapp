# Generated by Django 4.1.3 on 2022-12-22 18:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0057_alter_transaction_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='futurestrade',
            name='stop_price',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=12, null=True, verbose_name='손절가'),
        ),
    ]
