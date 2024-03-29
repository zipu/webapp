# Generated by Django 4.1.3 on 2022-12-21 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0055_futuresaccount_asset'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cashaccount',
            name='asset',
        ),
        migrations.DeleteModel(
            name='Record',
        ),
        migrations.RemoveField(
            model_name='futuresinstrument',
            name='closetime',
        ),
        migrations.RemoveField(
            model_name='futuresinstrument',
            name='opentime',
        ),
        migrations.AlterField(
            model_name='futuresinstrument',
            name='tickunit',
            field=models.DecimalField(decimal_places=8, max_digits=14, verbose_name='호가 단위'),
        ),
        migrations.DeleteModel(
            name='CashAccount',
        ),
    ]
