from django.db import models
from django.db.models import Avg, Sum, Max, StdDev
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
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

class FuturesSystem(models.Model):
    """ 시스템 """
    opendate = models.DateField("운용 시작일")
    name = models.CharField("시스템명", max_length=64)
    symbol = models.CharField("시스템코드", max_length=16)
    principal = models.PositiveIntegerField("투자원금(KRW)")
    count = models.PositiveIntegerField("매매횟수", null=True, blank=True)
    gross_return = models.FloatField("누적손익", default=0)
    gross_return_ratio = models.FloatField("누적수익률", default=0)
    average_ptr = models.FloatField("평균손익비", default=0)
    winning_rate = models.FloatField("승률", default=0)
    average_profit = models.FloatField("평균수익", default=0)
    std = models.FloatField("수익표준편차", default=0)
    dd = models.FloatField("자본인하율", default=0)
    mdd = models.FloatField("최대자본인하율", default=0)
    duration = models.PositiveIntegerField("평균보유기간", default=0)

    def __str__(self):
        return f"{self.name}"

class  FuturesEntry(models.Model):
    """ 진입 내역 abstract 모델"""
    POSITIONS = [
        (1, "Long"),
        (-1, "Short")
    ]
    system = models.ForeignKey(FuturesSystem,
                    verbose_name="시스템",
                    related_name="entries",
                    on_delete=models.PROTECT)
    date = models.DateField("진입 날짜")
    instrument = models.ForeignKey(Instrument, verbose_name="상품명", on_delete=models.PROTECT)
    position = models.SmallIntegerField("포지션", choices=POSITIONS)
    quantity = models.SmallIntegerField("계약수")
    price = models.FloatField("진입가")
    riskprice = models.FloatField("손절가")
    stopprice = models.FloatField("청산 예정가")
    commission = models.FloatField("수수료", default=0)
    cum_commission = models.FloatField("누적수수료", default=0)
    entryrisk = models.FloatField("진입 리스크", blank=True)
    is_open = models.BooleanField("매매 상태", default=True)

    def save(self, *args, **kwargs):
        self.entryrisk = int(round((self.price - self.riskprice)*self.position/self.instrument.tickunit))\
                      * float(self.instrument.tickprice) * self.quantity
        
        if FuturesEntry.objects.count() > 0:
            self.cum_commission = self.system.entries.filter(id__lte=self.system.entries.order_by('-id').first().id)\
                                  .aggregate(Sum('commission'))['commission__sum']\
                                  + self.commission
        else:
            self.cum_commission = self.commission
        super(FuturesEntry, self).save(*args, **kwargs)

    def __str__(self):
        return f"({self.id}) 상품: {self.instrument.name} / 날짜: {self.date}/ 리스크: {self.entryrisk}"

    class Meta:
        ordering = ('-id',)

class FuturesExit(models.Model):
    """ 청산 내역 Abstract model """
    date = models.DateField("청산날짜")
    entry = models.ForeignKey(FuturesEntry,
               related_name="exits",
               verbose_name="진입매매",
               on_delete=models.CASCADE)
    quantity = models.SmallIntegerField("계약수")
    price = models.FloatField("청산가격")
    profit = models.FloatField("손익", blank=True)
    cum_profit = models.FloatField("누적손익", blank=True)
    ptr = models.FloatField("손익비", blank=True)
    duration = models.DurationField("보유기간", blank=True)

    def save(self, *args, **kwargs):
        exits = FuturesExit.objects.filter(entry__system__id=self.entry.system.id)
        self.profit = int((self.price - self.entry.price)*self.entry.position/self.entry.instrument.tickunit)\
                       * float(self.entry.instrument.tickprice) * self.quantity
        if exits.count() > 0:
            self.cum_profit = exits.filter(id__lt=exits.all().order_by('-id').first().id)\
                              .aggregate(Sum('profit'))['profit__sum'] + self.profit
        else:
            self.cum_profit = self.profit
        self.ptr = abs(self.profit/self.entry.entryrisk) if self.profit > 0 else 0
        self.duration = self.date - self.entry.date
        super(FuturesExit, self).save(*args, **kwargs)

    def __str__(self):
        return f"id = {self.id}, entry id = {self.entry.id}: {self.profit} / {self.date}"


@receiver(post_save, sender=FuturesExit,
          dispatch_uid="update_system_summary")
def update_futures_system_summary(sender, instance, **kwargs):
    system = instance.entry.system
    exits = FuturesExit.objects.filter(entry__system__id=system.id)
    system.count = exits.count()
    agg = exits.aggregate(Sum('profit'), Avg('profit'), StdDev('profit')\
                        ,Max('cum_profit'), Avg('ptr'), Avg('duration'))
    system.gross_return = agg['profit__sum']
    system.average_profit = agg['profit__avg']
    system.std = agg['profit__stddev']
    system.gross_return_ratio = (system.gross_return / system.principal) * 100
    system.average_ptr = agg['ptr__avg']
    system.winning_rate = (exits.filter(profit__gt=0).count()/system.count)*100
    max_cum_profit = agg['cum_profit__max']
    system.dd = ((max_cum_profit - system.gross_return)/max_cum_profit)*100
    system.mdd = system.dd if system.dd > system.mdd else system.mdd
    system.duration = agg['duration__avg'].days
    system.save()




    
    
    
    
