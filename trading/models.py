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

    name = models.CharField("상품명", max_length=64) #상품명
    symbol = models.CharField("상품코드", max_length=16) #상품코드
    currency = models.CharField("거래 통화", max_length=16, choices=CURRENCIES, default='USD') #통화
    exchange = models.CharField("거래소", max_length=16, choices=EXCHANGES) #거래소
    market = models.CharField("시장 구분", max_length=16, choices=MARKETS) #시장구분
    tickunit = models.FloatField("호가 단위") #틱 단위
    tickprice = models.DecimalField("호가당 가격", max_digits=5, decimal_places=2) #틱당 가격
    margin = models.PositiveIntegerField("증거금") #증거금
    opentime = models.TimeField("거래 시작시간") #장 시작시간(한국)
    closetime = models.TimeField("거래 종료시간") #장 종료시간(한국)
    decimal_length = models.SmallIntegerField("소수점 자리수") #소수점 자리수

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class Entry(models.Model):
    """ 진입 내역 """
    POSITIONS = [
        (1, "Long"),
        (-1, "Short")
    ]
    date = models.DateTimeField("진입 날짜")
    instrument = models.ForeignKey(Instrument, verbose_name="상품명", on_delete=models.PROTECT)
    position = models.SmallIntegerField("포지션")
    quantity = models.SmallIntegerField("계약수")
    price = models.FloatField("진입가")
    stopprice = models.FloatField("청산 예정가")
    risk = models.FloatField("매매리스크")

    def save(self, *args, **kwargs):
        self.risk = int((self.price - self.stopprice)*self.position/self.instrument.tickunit)\
                      * self.instrument.tickprice * self.quantity
        super(Entry, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.instrument.name}/{self.date}/{self.risk}"


class Exit(models.Model):
    """ 청산 내역 """
    pass
    
    
    
