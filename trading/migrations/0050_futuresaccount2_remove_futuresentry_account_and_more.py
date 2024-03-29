# Generated by Django 4.1.3 on 2022-12-21 11:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0049_delete_currencyrates_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FuturesAccount2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='날짜')),
                ('account_name', models.CharField(default='futures', max_length=20, verbose_name='계좌명')),
                ('symbol', models.CharField(default='F', max_length=16, verbose_name='계좌코드')),
                ('principal_krw', models.DecimalField(decimal_places=0, max_digits=12, verbose_name='시드(원)')),
                ('pricnipal_usd', models.DecimalField(decimal_places=1, max_digits=12, verbose_name='시드(달러)')),
                ('principal', models.DecimalField(blank=True, decimal_places=0, max_digits=12, verbose_name='총시드(원)')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='futures', to='trading.asset', verbose_name='자산종류')),
            ],
        ),
        migrations.RemoveField(
            model_name='futuresentry',
            name='account',
        ),
        migrations.RemoveField(
            model_name='futuresentry',
            name='instrument',
        ),
        migrations.RemoveField(
            model_name='futuresentry',
            name='strategy',
        ),
        migrations.RemoveField(
            model_name='futuresexit',
            name='entry',
        ),
        migrations.DeleteModel(
            name='FuturesAccount',
        ),
        migrations.DeleteModel(
            name='FuturesEntry',
        ),
        migrations.DeleteModel(
            name='FuturesExit',
        ),
    ]
