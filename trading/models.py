from django.db import models

# Create your models here.
from django.db import models
from datetime import datetime

class Instrument(models.Model):
    """
    상품 정보 모델
    """
    CURRENCIES = [
        ('USD', 'Dollar'),
        ('EUR', 'EURO'),
        ('HKD', 'Hongkong Dollar'),
        ('JYP', 'Japanese Yen')
    ]

    EXCHANGES = [
        ('CME', 'CME'),
        ('NYMEX', 'NYMEX'),
        ('CBOE', 'CBOE'),
        ('CBOT', 'CBOT'),
        ('EUREX', 'EUREX'),
        ('HKEX', 'HKEX'),
        ('SGX', 'SGX'),
        ('ICE_US', 'ICE_US')
    ]

    MARKETS = [
        ('CUR', '통화'),
        ('IDX', '지수'),
        ('INT', '금리'),
        ('ENG', '에너지'),
        ('MTL', '금속'),
        ('Grain', '곡물'),
        ('Tropical', '열대과일'),
        ('Meat', '육류')
    ]

    name = models.CharField(max_length=64) #상품명
    symbol = models.CharField(max_length=16) #상품코드
    currency = models.CharField(max_length=16, choices=CURRENCIES, default='USD') #통화
    exchange = models.CharField(max_length=16, choices=EXCHANGES) #거래소
    market = models.CharField(max_length=16, choices=MARKETS) #시장구분
    tickunit = models.FloatField() #틱 단위
    tickprice = models.DecimalField(max_digits=5, decimal_places=2) #틱당 가격
    margin = models.PositiveIntegerField() #증거금
    opentime = models.TimeField() #장 시작시간(한국)
    closetime = models.TimeField() #장 종료시간(한국)
    decimal_length = models.SmallIntegerField() #소수점 자리수

    def __str__(self):
        return f"{self.name} ({self.symbol})"

