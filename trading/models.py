from django.db import models
from django.db.models import Avg, Sum, Max, StdDev, F, ExpressionWrapper
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ImproperlyConfigured

# Create your models here.
from decimal import Decimal as D
from forex_python.converter import CurrencyRates

##############################################
# 선물 거래 관련 모델                         #
##############################################
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
    tickunit = models.DecimalField("호가 단위", max_digits=12, decimal_places=6) #틱 단위
    tickprice = models.DecimalField("호가당 가격", max_digits=5, decimal_places=2) #틱당 가격
    margin = models.DecimalField("증거금", max_digits=5, decimal_places=0) #증거금
    decimal_places = models.SmallIntegerField("소수점 자리수") #소수점 자리수
    current_price = models.DecimalField("현재가", max_digits=12, decimal_places=6, null=True, blank=True)
    opentime = models.TimeField("거래 시작시간") #장 시작시간(한국)
    closetime = models.TimeField("거래 종료시간") #장 종료시간(한국)

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class FuturesSystem(models.Model):
    """ 시스템 """
    opendate = models.DateField("운용 시작일")
    name = models.CharField("시스템명", max_length=64)
    symbol = models.CharField("시스템코드", max_length=16)
    principal_krw = models.DecimalField("투자원금(KRW)", max_digits=9, decimal_places=0)
    principal_usd = models.DecimalField("투자원금(USD)", max_digits=6, decimal_places=0, blank=True)
    
    def save(self, *args, **kwargs):
        c = CurrencyRates()
        self.principal_usd = c.convert('KRW', 'USD', self.principal_krw)
        super(FuturesSystem, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}/{self.name}"

class FuturesTrackRecord(models.Model):
    
    system = models.ForeignKey(
        FuturesSystem,
        verbose_name="시스템실적",
        related_name="records",
        on_delete=models.CASCADE)
    date = models.DateTimeField("날짜", auto_now_add=True)
    entry = models.ForeignKey("trading.FuturesEntry", on_delete=models.CASCADE, null=True, blank=True)
    exit = models.ForeignKey("trading.FuturesExit", on_delete=models.CASCADE, null=True, blank=True)
    count = models.PositiveIntegerField("매매횟수")
    gross_return = models.DecimalField("누적손익(달러)", max_digits=9, decimal_places=2)
    gross_return_krw = models.DecimalField("누적손익(원)", max_digits=10, decimal_places=0)
    gross_return_ratio = models.FloatField("누적수익률")
    average_ptr = models.FloatField("평균손익비")
    winning_rate = models.FloatField("승률")
    average_profit = models.DecimalField("평균수익", max_digits=9, decimal_places=2)
    average_profit_krw = models.DecimalField("평균수익(원)", max_digits=10, decimal_places=0)
    std = models.DecimalField("수익표준편차", max_digits=9, decimal_places=2)
    std_krw = models.DecimalField("수익표준편차(원)", max_digits=12, decimal_places=0)
    dd = models.FloatField("자본인하율")
    mdd = models.FloatField("최대자본인하율")
    duration = models.PositiveIntegerField("평균보유기간")
    risk_per_trade = models.DecimalField("매매당리스크", max_digits=9, decimal_places=2)
    risk = models.DecimalField("현재총리스크", max_digits=9, decimal_places=2)
    risk_per_trade_krw = models.DecimalField("매매당리스크(원)", max_digits=9, decimal_places=0, blank=True)
    risk_krw = models.DecimalField("현재총리스크(원)", max_digits=9, decimal_places=0, blank=True)
    commission = models.DecimalField("누적수수료", max_digits=9, decimal_places=2)
    commission_krw = models.DecimalField("누적수수료(원)", max_digits=12, decimal_places=0)


    def save(self, *args, **kwargs):
        c = CurrencyRates()
        self.gross_return_krw = c.convert('USD', 'KRW', self.gross_return)
        self.average_profit_krw =  c.convert('USD', 'KRW', self.average_profit)
        self.std_krw = c.convert('USD', 'KRW', self.std)
        self.risk_krw = c.convert('USD', 'KRW', self.risk)
        self.risk_per_trade_krw = c.convert('USD', 'KRW', self.risk_per_trade)
        self.commission_krw = c.convert('USD', 'KRW', self.commission)
        super(FuturesTrackRecord, self).save(*args, **kwargs)

    def __str__(self):
        return f"({self.date}) {self.system.name} 운용실적"

    class Meta:
        ordering = ('-date',)


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
    price = models.DecimalField("진입가", max_digits=12, decimal_places=6)
    riskprice = models.DecimalField("손절가", max_digits=12, decimal_places=6, blank=True)
    stopprice = models.DecimalField("청산 예정가", max_digits=12, decimal_places=6)
    open_cons = models.SmallIntegerField("미청산계약수")
    close_cons = models.SmallIntegerField("청산계약수", default=0)
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=2)
    commission_krw = models.DecimalField("수수료(원)", blank=True, max_digits=9, decimal_places=0)
    entry_risk = models.DecimalField("진입 리스크", blank=True, max_digits=7, decimal_places=2)
    current_risk = models.DecimalField("현재 리스크", blank=True, max_digits=7, decimal_places=2)
    is_open = models.BooleanField("상태", default=True)

    def save(self, *args, **kwargs):
        c = CurrencyRates()
        
        if not self.id:
            self.entry_risk = ((self.price - self.riskprice)*self.position/self.instrument.tickunit)\
                             *self.instrument.tickprice*self.quantity
            self.commission_krw = c.convert('USD', 'KRW', self.commission)
        current_risk = ((self.price - self.stopprice)*self.position/self.instrument.tickunit)\
                         *self.instrument.tickprice*self.open_cons
        self.current_risk = current_risk if current_risk > 0 else 0
        
        self.is_open = True if self.open_cons > 0 else False
        super(FuturesEntry, self).save(*args, **kwargs)

    def __str__(self):
        return f"({self.id}) 상품: {self.instrument.name} / 날짜: {self.date}/ 리스크: {self.entry_risk}"

    class Meta:
        ordering = ('-id',)

class FuturesExit(models.Model):
    """ 청산 내역 Abstract model """
    date = models.DateField("청산날짜")
    entry = models.ForeignKey(
               FuturesEntry,
               related_name="exits",
               verbose_name="진입매매",
               on_delete=models.CASCADE)
    quantity = models.SmallIntegerField("계약수")
    price = models.DecimalField("청산가격", max_digits=12, decimal_places=6)
    profit = models.DecimalField("손익", blank=True, max_digits=9, decimal_places=2)
    profit_krw = models.DecimalField("손익(원)", blank=True, max_digits=10, decimal_places=0)
    duration = models.DurationField("보유기간", blank=True)

    def save(self, *args, **kwargs):
        if self.id:
            raise ImproperlyConfigured("FuturesExit은 수정할수 없습니다. 삭제 후 다시 작성하세요")
            #raise ValueError("FuturesExit은 수정할수 없습니다. 삭제 후 다시 작성하세요")

        self.profit = ((self.price - self.entry.price)*self.entry.position/self.entry.instrument.tickunit)\
                       * (self.entry.instrument.tickprice) * self.quantity
        self.duration = self.date - self.entry.date
        c = CurrencyRates()
        self.profit_krw = c.convert('USD', 'KRW', self.profit)
        super(FuturesExit, self).save(*args, **kwargs)

    def __str__(self):
        return f"id = {self.id}, entry id = {self.entry.id}: {self.profit} / {self.date}"
    
    class Meta:
        ordering = ('-id',)


@receiver(post_save, sender=FuturesEntry,
          dispatch_uid="update_system_record")
@receiver(post_save, sender=FuturesExit,
          dispatch_uid="update_system_record")
def update_futures_system_record(sender, instance, **kwargs):
    if isinstance(instance, FuturesEntry):
        system = instance.system
        record = FuturesTrackRecord(system=system, entry=instance)
    
    if isinstance(instance, FuturesExit):
        #미청산 계약수 갱신
        system = instance.entry.system
        record = FuturesTrackRecord(system=system, exit=instance)
        entry = instance.entry
        close_cons = entry.exits.all().aggregate(Sum('quantity'))['quantity__sum']
        open_cons = entry.quantity - close_cons
        risk = ((entry.price - entry.stopprice)*entry.position/entry.instrument.tickunit)\
                             *entry.instrument.tickprice*entry.open_cons
        current_risk = risk if risk > 0 else 0
        
        is_open = True if open_cons > 0 else False
        FuturesEntry.objects.filter(id=entry.id).update(
            close_cons=close_cons, open_cons=open_cons, current_risk=current_risk, is_open=is_open
        )

    
    #시스템 운용 현황 갱신
    
    entries = system.entries.all()
    exits = FuturesExit.objects.filter(entry__system__id=system.id)

    agg_entry = entries.aggregate(Avg('entry_risk'), Sum('commission'))
    agg_exits = exits.aggregate(Avg('profit'), Sum('profit'), StdDev('profit')\
                                ,Avg('duration'))
    
    record.risk = entries.filter(is_open=True).aggregate(Sum('current_risk'))['current_risk__sum'] or 0
    record.risk_per_trade = agg_entry['entry_risk__avg']
    record.commission = agg_entry['commission__sum']
        
    if exits.count() == 0:
        record.count = 0
        record.gross_return = 0
        record.gross_return_ratio =  0
        record.average_profit = 0
        record.average_ptr = 0
        record.winning_rate = 0
        record.duration = 0
        record.std = 0
        record.dd = 0
        record.mdd = 0

    else:
        record.count = exits.count()
        record.gross_return = agg_exits['profit__sum']
        record.gross_return_ratio = (record.gross_return / system.principal_usd)*100
        record.average_profit = agg_exits['profit__avg']
        avg_gain = exits.filter(profit__gt=0).aggregate(Avg('profit'))['profit__avg'] or 0
        avg_loss = exits.filter(profit__lt=0).aggregate(Avg('profit'))['profit__avg'] or 0
        record.average_ptr = abs(avg_gain/avg_loss) if avg_loss != 0 else 1
        record.winning_rate = (exits.filter(profit__gt=0).count()/record.count)*100
        record.std = agg_exits['profit__stddev']
        record.duration = agg_exits['duration__avg'].days
        
        agg_records = FuturesTrackRecord.objects.all().aggregate(Max('gross_return'), Max('dd'))
        
        max_gross_return = agg_records['gross_return__max'] or 0
        max_dd = agg_records['dd__max'] or 0
        new_max_gross_return = max(max_gross_return, record.gross_return)
        record.dd = ((new_max_gross_return - record.gross_return)/(new_max_gross_return + system.principal_usd))*100
        record.mdd = max(max_dd, record.dd)

    record.save()



##############################################
# 주식/ETF 거래 관련 모델                     #
##############################################
class StockSummary(models.Model):
    date = models.DateField("날짜", auto_now_add=True)
    principal = models.DecimalField("투자원금", max_digits=10, decimal_places=0)
    cash = models.DecimalField("보유현금", max_digits=10, decimal_places=0)
    stock = models.DecimalField("주식가치", max_digits=10, decimal_places=0)
    profit = models.DecimalField("누적수익", max_digits=10, decimal_places=0, default=0)
    rate_of_return = models.FloatField("수익률", default=0)

class StockStatement(models.Model):
    """ 주식 거래 명세"""
    date = models.DateField("매매시작일")
    name = models.CharField("종목명", max_length=50)
    code = models.CharField("종목코드", max_length=10)
    current_price = models.DecimalField("현재가", max_digits=10, decimal_places=0) 
    stop_price = models.DecimalField("청산예정가", max_digits=10, decimal_places=0)
    purchase_money = models.DecimalField("총매입금", max_digits=10, decimal_places=0, default=0)
    buy_quantity = models.PositiveIntegerField("총매입주식수", default=0)
    sell_quantity = models.PositiveIntegerField("총청산주식수", default=0)
    quantity = models.PositiveIntegerField("보유주식수", default=0)
    average_purchase_price = models.DecimalField("평균매수단가", max_digits=10, decimal_places=0, default=0)
    average_sell_price = models.DecimalField("평균매도단가", max_digits=10, decimal_places=0, default=0)
    stock_value = models.DecimalField("주식가치", max_digits=10, decimal_places=0, default=0)
    liquidation = models.DecimalField("총청산금", max_digits=10, decimal_places=0, default=0)
    dividends = models.DecimalField("배당금", max_digits=10, decimal_places=0, default=0)
    is_open = models.BooleanField("매매상태", default=True)

    def save(self, *args, **kwargs):
        if self.buys.count() > 0:
            agg = self.buys.aggregate(Sum('quantity'), Sum('purchase_money'))
            self.buy_quantity = agg['quantity__sum']
            self.purchase_money = agg['purchase_money__sum']
            self.average_purchase_price = self.purchase_money / self.buy_quantity
        
        if self.sells.count() > 0:
            agg = self.sells.aggregate(Sum('quantity'), Sum('liquidation'))
            self.sell_quantity = agg['quantity__sum']
            self.liquidation = agg['liquidation__sum']
            self.average_sell_price = self.liquidation / self.sell_quantity

        self.quantity = self.buy_quantity - self.sell_quantity
        self.stock_value = self.quantity * self.current_price
        self.is_open = False if self.quantity == 0 else True

        super(StockStatement, self).save(*args, **kwargs)

    def __str__(self):
        return(f"{self.date}/{self.name}")
    
    class Meta:
        ordering = ('-id',)
    
class StockBuy(models.Model):
    trade = models.ForeignKey(
        StockStatement,
        verbose_name="매매",
        related_name="buys",
        on_delete=models.CASCADE)
    date = models.DateField("진입일")
    quantity = models.PositiveIntegerField("매수수량")
    price = models.DecimalField("매수가격", max_digits=10,decimal_places=0)
    purchase_money = models.DecimalField("매입금액", max_digits=10, decimal_places=0, blank=True)

    def save(self, *args, **kwargs):
        self.purchase_money = self.quantity * self.price
        super(StockBuy, self).save(*args, **kwargs)

    def __str__(self):
        return(f"{self.date}/{self.trade.name}")


class StockSell(models.Model):
    trade = models.ForeignKey(
        StockStatement,
        verbose_name="매매",
        related_name="sells",
        on_delete=models.CASCADE)
    date = models.DateField("청산일")
    quantity = models.PositiveIntegerField("청산수량")
    price = models.DecimalField("청산가격", max_digits=10, decimal_places=0)
    liquidation = models.DecimalField("청산금액", max_digits=10, decimal_places=0, blank=True)

    def save(self, *args, **kwargs):
        self.liquidation = self.price * self.quantity
        super(StockSell, self).save(*args, **kwargs)

    def __str__(self):
        return(f"{self.date}/{self.trade.name}")


@receiver(post_save, sender=StockBuy, dispatch_uid="update_stock_statement")
@receiver(post_save, sender=StockSell, dispatch_uid="update_stock_statement")
def update_stock_statement(sender, instance, **kwargs):
    instance.trade.save()

@receiver(post_save, sender=StockStatement, dispatch_uid="update_stock_summary")
def update_stock_statement_at_entry(sender, instance, **kwargs):
    principal = StockSummary.objects.all().first().principal
    summary = StockSummary()

    
    agg = StockStatement.objects.all().aggregate(
        Sum('purchase_money'),
        Sum('stock_value'),
        Sum('liquidation'))
    summary.principal = principal
    summary.cash = principal + agg['liquidation__sum'] - agg['purchase_money__sum']
    summary.stock = agg['stock_value__sum']
    summary.profit = summary.cash + summary.stock - summary.principal
    summary.rate_of_return = (summary.profit/ summary.principal) * 100
    summary.save()








    



    
    
    
    
