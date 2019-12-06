# Generated by Django 2.2.6 on 2019-12-06 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0004_transfer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transfer',
            name='amount_from',
            field=models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True, verbose_name='출금액'),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='currency_from',
            field=models.CharField(blank=True, choices=[('KRW', '원'), ('USD', '달러'), ('CNY', '위안')], max_length=10, null=True, verbose_name='출금통화'),
        ),
    ]
