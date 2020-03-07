# Generated by Django 3.0.3 on 2020-03-07 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0011_futuresexit_commission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='futuresaccount',
            name='principal_eur',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=11, verbose_name='투자원금(EUR)'),
        ),
        migrations.AlterField(
            model_name='futuresaccount',
            name='principal_usd',
            field=models.DecimalField(decimal_places=2, max_digits=11, verbose_name='투자원금(USD)'),
        ),
        migrations.AlterField(
            model_name='futuresaccount',
            name='value_eur',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=11, verbose_name='유로자산가치(EUR)'),
        ),
        migrations.AlterField(
            model_name='futuresaccount',
            name='value_usd',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=11, verbose_name='달러자산가치(USD)'),
        ),
    ]
