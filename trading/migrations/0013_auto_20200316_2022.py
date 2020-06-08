# Generated by Django 3.0.3 on 2020-03-16 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0012_auto_20200307_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transfer',
            name='amount_from',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True, verbose_name='출금액'),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='amount_to',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='입금액'),
        ),
    ]
