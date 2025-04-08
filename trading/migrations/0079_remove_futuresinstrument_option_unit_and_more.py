# Generated by Django 4.1.3 on 2025-04-07 15:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0078_alter_currency_date_and_more'),
    ]

    operations = [
        #migrations.RemoveField(
        #    model_name='futuresinstrument',
        #    name='option_unit',
        #),
        #migrations.RemoveField(
        #    model_name='futuresinstrument',
        #    name='option_weight',
        #),
        migrations.AddField(
            model_name='futuresinstrument',
            name='kiwoom_symbol',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='키움상품코드'),
        ),
        migrations.AlterField(
            model_name='futuresinstrument',
            name='exchange',
            field=models.CharField(choices=[('CME', 'CME'), ('NYMEX', 'NYMEX'), ('CBOE', 'CBOE'), ('CBOT', 'CBOT'), ('EUREX', 'EUREX'), ('HKEX', 'HKEX'), ('SGX', 'SGX'), ('ICE_US', 'ICE_US'), ('STOCK OPTION', 'STOCK OPTION')], max_length=16, verbose_name='거래소'),
        ),
        migrations.AlterField(
            model_name='futuresinstrument',
            name='market',
            field=models.CharField(choices=[('CUR', '통화'), ('IDX', '지수'), ('INT', '금리'), ('ENG', '에너지'), ('MTL', '금속'), ('Grain', '곡물'), ('Tropical', '열대과일'), ('Meat', '육류'), ('Stock', '주식')], max_length=16, verbose_name='시장 구분'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='type',
            field=models.CharField(choices=[('Futures', 'Futures'), ('Option', 'Option'), ('Spread', 'Spread'), ('StockOption', 'StockOption')], default='Futures', max_length=20, verbose_name='타입'),
        ),
        migrations.CreateModel(
            name='KiwoomPosition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('amount_buy', models.PositiveIntegerField(blank=True, null=True, verbose_name='매수보유수량')),
                ('amount_sell', models.PositiveIntegerField(blank=True, null=True, verbose_name='매도보유수량')),
                ('percent_buy', models.PositiveIntegerField(blank=True, null=True, verbose_name='매수비율')),
                ('percent_sell', models.PositiveIntegerField(blank=True, null=True, verbose_name='매도비율')),
                ('instrument', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='trading.futuresinstrument')),
            ],
        ),
    ]
