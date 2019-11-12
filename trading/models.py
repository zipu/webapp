from django.db import models

from django.db.models import Avg, Sum, Max, StdDev, F, ExpressionWrapper
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
from decimal import Decimal as D
from datetime import datetime, timedelta, time

from forex_python.converter import CurrencyRates

def create_record(account):
    now = datetime.now()
    if account=='all':
        create_record('cash')
        create_record('stock')
        create_record('futures')
        create_record('asset')

    if account=='asset':
        stock = StockAccount.objects.all().first()
        cash = CashAccount.objects.all().latest('date')
        futures = FuturesAccount.objects.all()

        principal = stock.principal + cash.total\
                    + futures.aggregate(Sum('principal'))['principal__sum']
        value = stock.value + cash.total\
                    + futures.aggregate(Sum('value'))['value__sum']
        risk = stock.risk + futures.aggregate(Sum('risk'))['risk__sum']
        Record(
            date=now,
            account_symbol='A', #total asset
            principal=principal,
            value=value,
            risk=risk
        ).save()

    elif account=='cash':
        acc = CashAccount.objects.all().latest('date')
        Record(
            date=now,
            account_symbol=acc.symbol,
            principal=acc.total,
            value=acc.total,
            risk=0
        ).save()
    
    elif account=='stock':
        acc = StockAccount.objects.all().first()
        Record(
            date=now,
            account_symbol=acc.symbol,
            principal=acc.principal,
            value=acc.value,
            risk=acc.risk
        ).save()
    
    elif account=='futures':
        accounts = FuturesAccount.objects.all()
        for acc in accounts:
            Record(
                date=now,
                account_symbol=acc.symbol,
                principal=acc.principal,
                value=acc.value,
                risk=acc.risk
            ).save()



##############################################
# 공통                                       #
##############################################
class Asset(models.Model):
    CODES = [
        ('C', 'Cash'),
        ('S', 'Stock'),
        ('F', 'Futures')
    ]
    name = models.CharField("자산명", max_length=50)
    code = models.CharField("자산코드", choices=CODES, max_length=10)
    description = models.TextField("설명", null=True, blank=True)
    def __str__(self):
        return f"{self.name}({self.code})"

class Record(models.Model):
    """ 날짜별 자산 실적/평가가치/통계 """
    account_symbol = models.CharField("계좌코드", max_length=50)
    #account_id = models.PositiveIntegerField("account_id")
    date = models.DateTimeField("날짜", auto_now_add=False)
    principal = models.DecimalField("원금(원)", max_digits=12, decimal_places=0)
    value = models.DecimalField("총자산(원)", max_digits=12, decimal_places=0)
    risk = models.DecimalField("리스크(원)", max_digits=12, decimal_places=0)
    # save method에서 계산
    gross_profit = models.DecimalField("누적수익(원)", max_digits=12, decimal_places=0)
    risk_excluded_value = models.DecimalField("위험제거자산(원)", max_digits=12, decimal_places=0)
    rate_profit = models.FloatField("수익률")
    rate_risk = models.FloatField("리스크율")
    avg_risk = models.DecimalField("평균리스크", max_digits=12, decimal_places=0)
    drawdown = models.FloatField("자본인하율")
    mdd = models.FloatField("최대자본인하율")
    cagr = models.FloatField("CAGR", blank=True)
    volatility_day = models.FloatField("일변동성") 
    volatility = models.FloatField("평균변동성") #최근 30일 변동성

    def save(self, *args, **kwargs):
        self.gross_profit = self.value - self.principal
        self.risk_excluded_value = self.value - self.risk
        self.rate_profit =  self.gross_profit/self.principal * 100
        self.rate_risk = self.risk/self.value * 100
        
        if not self.id:
            records = Record.objects.filter(account_symbol=self.account_symbol).all()
        else:
            records = Record.objects.filter(account_symbol=self.account_symbol, id__lt=self.id).all()
        
        if records.count():
            last_value = records.latest('date').value
            last_mdd = records.latest('date').mdd
            last_max = records.aggregate(Max('value'))['value__max']
            
            self.avg_risk = records.aggregate(Avg('risk'))['risk__avg']
            self.volatility_day = 100*abs(last_value-self.value)/last_value
            
            since = self.date - timedelta(days=30)
            self.volatility = records.filter(date__gte=since).all()\
                            .aggregate(Avg('volatility_day'))['volatility_day__avg']
            
            max_value = max(last_max, self.value)
            self.drawdown = 100 * (max_value - self.value)/max_value
            self.mdd = max(self.drawdown, last_mdd)

            #계좌오픈일 찾기
            if self.account_symbol == 'A':
                first_date = CashAccount.objects.all().earliest('date').date
            elif self.account_symbol == 'C':
                first_date = CashAccount.objects.all().earliest('date').date
            elif self.account_symbol == 'S':
                first_date = StockAccount.objects.first().date
            else:
                first_date = FuturesAccount.objects.get(symbol=self.account_symbol).date

            days = (self.date.date() - first_date).days
            if days > 1:
                n = days/365
                self.cagr = (pow(float(self.value/self.principal), 1/n) - 1)*100
            else:
                self.cagr = 0

        else:
            last_mdd = 0
            last_max = 0
            last_value = 0
            self.volatility_day=0
            self.volatility=0
            self.avg_risk = 0
            self.cagr = 0
            self.drawdown = 0
            self.mdd = 0

        super(Record, self).save(*args, **kwargs)    
    def __str__(self):
        return f"{self.id}/{self.account_symbol}/{self.date}/{self.value}"
    class Meta:
        ordering = ['-id']
    
##############################################
# 현금                                       #
##############################################
class CashAccount(models.Model):
    asset = models.ForeignKey(
        Asset,
        related_name="cash",
        verbose_name="자산종류",
        on_delete=models.CASCADE)
    date = models.DateField("날짜")
    account_name = models.CharField("계좌명", max_length=20, default='cash')
    symbol = models.CharField("계좌코드", max_length=16, default='C')
    krw = models.DecimalField("원화", max_digits=12, decimal_places=0)
    cny = models.DecimalField("위안화", max_digits=12, decimal_places=0)
    usd = models.DecimalField("달러", max_digits=12, decimal_places=0)
    total = models.DecimalField("합계(원)",blank=True, max_digits=12, decimal_places=0)

    def save(self, *args, **kwargs):
        c = CurrencyRates()
        self.total = c.convert('USD','KRW',self.usd)+\
                c.convert('CNY','KRW',self.cny)+\
                self.krw
        
        super(CashAccount, self).save(*args, **kwargs)
    def __str__(self):
        return f"{self.total} won - {self.date}"
    

##############################################
# 주식/ETF                                   #
##############################################
class StockAccount(models.Model):
    asset = models.ForeignKey(
        Asset,
        related_name="stocks",
        verbose_name="주식자산",
        on_delete=models.CASCADE)
    account_name = models.CharField("계좌명", max_length=20, default='stock', editable=False)
    symbol = models.CharField("계좌코드", max_length=16, default='S')
    date = models.DateField("날짜")
    principal = models.DecimalField("투자원금", max_digits=12, decimal_places=0)
    value = models.DecimalField("총자산가치", max_digits=12, decimal_places=0, blank=True)
    balance = models.DecimalField("계좌잔고", max_digits=12, decimal_places=0, blank=True)
    value_stock = models.DecimalField("주식가치", max_digits=12, decimal_places=0, blank=True)
    dividends = models.DecimalField("배당금", max_digits=12, decimal_places=0, blank=True)
    risk = models.DecimalField("리스크", max_digits=10, decimal_places=0, blank=True)
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=0, blank=True)

    def save(self,*args, **kwargs):
        if not self.id:
            super(StockAccount, self).save(*args, **kwargs)
            return
        
        opens_agg = self.trades.filter(is_open=True).aggregate(
            Sum('value_stock'),
            Sum('risk'))
        agg = self.trades.all().aggregate(
            Sum('liquidation'),
            Sum('dividends'),
            Sum('commission'))

        purchase_amount=StockBuy.objects.filter(trade__account=self)\
            .aggregate(Sum('purchase_amount'))['purchase_amount__sum'] or 0
        liquidation = agg['liquidation__sum'] or 0
        self.value_stock = opens_agg['value_stock__sum'] or 0
        self.dividends = agg['dividends__sum'] or 0
        self.commission = agg['commission__sum'] or 0
        self.value = self.principal + self.value_stock + self.dividends +liquidation\
                   -  purchase_amount - self.commission
        self.balance = self.value - self.value_stock
        self.risk = opens_agg['risk__sum'] or 0
        super(StockAccount, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"주식계좌_{self.id}"

class StockTradeUnit(models.Model):
    "주식 매매 단위"
    account = models.ForeignKey(
        StockAccount,
        related_name="trades",
        verbose_name="계좌",
        on_delete=models.CASCADE)
    date = models.DateField("매매시작일")
    name = models.CharField("종목명", max_length=50)
    code = models.CharField("종목코드", max_length=10)
    cur_stock_price = models.DecimalField("주식현재가", max_digits=10, decimal_places=0) 
    stop_price = models.DecimalField("청산예정가", max_digits=10, decimal_places=0)
    purchase_amount = models.DecimalField("매입금", max_digits=10, decimal_places=0, default=0, blank=True)
    num_buy = models.PositiveIntegerField("총매입주식수", default=0, blank=True)
    num_sell = models.PositiveIntegerField("총청산주식수", default=0, blank=True)
    num_hold = models.PositiveIntegerField("보유주식수", default=0, blank=True)
    avg_buy_price = models.DecimalField("평균매수단가", max_digits=12, decimal_places=2, default=0, blank=True)
    avg_sell_price = models.DecimalField("평균매도단가", max_digits=12, decimal_places=2, default=0, blank=True)
    value_stock = models.DecimalField("주식가치", max_digits=10, decimal_places=0, default=0, blank=True)
    liquidation = models.DecimalField("총청산금", max_digits=10, decimal_places=0, default=0, blank=True)
    dividends = models.DecimalField("배당금", max_digits=10, decimal_places=0, default=0, blank=True)
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=0, default=0, blank=True)
    risk = models.DecimalField("리스크", max_digits=10, decimal_places=0, default=0, blank=True)
    is_open = models.BooleanField("매매상태", default=True)

    def save(self, *args, **kwargs):
        if self.buys.count() > 0:
            agg = self.buys.aggregate(
                Sum('num_buy'), Sum('purchase_amount'), Sum('commission'))
            self.num_buy = agg['num_buy__sum']
            total_purchase_amount = agg['purchase_amount__sum']
            self.avg_buy_price = total_purchase_amount / self.num_buy
            buy_com = agg['commission__sum']
        else:
            self.num_buy = 0
            self.avg_buy_price = 0
            buy_com = 0

        if self.sells.count() > 0:
            agg = self.sells.aggregate(Sum('num_sell'), Sum('liquidation'),Sum('commission'))
            self.num_sell = agg['num_sell__sum']
            self.liquidation = agg['liquidation__sum']
            self.avg_sell_price = self.liquidation / self.num_sell
            sel_com = agg['commission__sum']
        
        else:
            self.num_sell=0
            self.liquidation=0
            self.avg_sell_price=0
            sel_com = 0

        self.commission = buy_com + sel_com 
        self.num_hold = self.num_buy - self.num_sell
        self.purchase_amount = self.avg_buy_price * self.num_hold
        self.value_stock = self.num_hold * self.cur_stock_price
        self.risk = (self.cur_stock_price - self.stop_price)*self.num_hold
        self.is_open = False if self.num_hold == 0 else True
        super(StockTradeUnit, self).save(*args, **kwargs)

    def __str__(self):
        return(f"{self.date}/{self.name}")
    
    class Meta:
        ordering = ('-id',)
    
class StockBuy(models.Model):
    trade = models.ForeignKey(
        StockTradeUnit,
        verbose_name="매매",
        related_name="buys",
        on_delete=models.CASCADE)
    date = models.DateField("진입일")
    num_buy = models.PositiveIntegerField("매수수량")
    price = models.DecimalField("매수가격", max_digits=10,decimal_places=0)
    commission = models.DecimalField("수수료", max_digits=9, decimal_places=0)
    purchase_amount = models.DecimalField("매입금액", max_digits=10, decimal_places=0, blank=True)
    
    def save(self, *args, **kwargs):
        self.purchase_amount = self.num_buy * self.price
        super(StockBuy, self).save(*args, **kwargs)
    def __str__(self):
        return(f"{self.date}/{self.trade.name}/{self.purchase_amount}")


class StockSell(models.Model):
    trade = models.ForeignKey(
        StockTradeUnit,
        verbose_name="매매",
        related_name="sells",
        on_delete=models.CASCADE)
    date = models.DateField("청산일")
    num_sell = models.PositiveIntegerField("청산수량")
    price = models.DecimalField("청산가격", max_digits=10, decimal_places=0)
    liquidation = models.DecimalField("청산금액", max_digits=10, decimal_places=0, blank=True)
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=0)
    def save(self, *args, **kwargs):
        self.liquidation = self.price * self.num_sell
        super(StockSell, self).save(*args, **kwargs)
    def __str__(self):
        return(f"{self.date}/{self.trade.name}/{self.liquidation}")


@receiver(post_save, sender=StockBuy, dispatch_uid="update_stock_statement")
@receiver(post_save, sender=StockSell, dispatch_uid="update_stock_statement")
def update_stock_statement(sender, instance, **kwargs):
    instance.trade.save()

@receiver(post_save, sender=StockTradeUnit, dispatch_uid="update_stock_account")
def update_stock_account(sender, instance, **kwargs):
    instance.account.save()

##############################################
# 선물 거래 관련 모델                         #
##############################################
class FuturesInstrument(models.Model):
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


class FuturesAccount(models.Model):
    asset = models.ForeignKey(
        Asset,
        related_name="futures",
        verbose_name="선물자산",
        on_delete=models.CASCADE)
    account_name = models.CharField("시스템명", max_length=64)
    date = models.DateField("운용 시작일")
    symbol = models.CharField("시스템코드", max_length=16)
    principal = models.DecimalField("투자원금", max_digits=12, decimal_places=0, blank=True)
    principal_krw = models.DecimalField("투자원금(KRW)", max_digits=9, decimal_places=0)
    principal_usd = models.DecimalField("투자원금(USD)", max_digits=9, decimal_places=0)
    value = models.DecimalField("총자산가치", max_digits=12, decimal_places=0, blank=True)
    gross_profit = models.DecimalField("누적수익", max_digits=12, decimal_places=0, blank=True)
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=0, blank=True)
    avg_ptr = models.FloatField("평균손익비", blank=True)
    winning_rate = models.FloatField("승률", blank=True)
    avg_profit = models.DecimalField("평균수익", max_digits=12, decimal_places=0, blank=True)
    std = models.DecimalField("수익표준편차", max_digits=12, decimal_places=0, blank=True)
    duration = models.PositiveIntegerField("평균보유기간", blank=True)
    avg_entry_risk = models.DecimalField("평균진입리스크", max_digits=12, decimal_places=0, blank=True)
    risk = models.DecimalField("현재총리스크", max_digits=12, decimal_places=0, blank=True)
    count = models.PositiveIntegerField("매매횟수", default=0)

    def save(self, *args, **kwargs):
        c = CurrencyRates()
        if not self.id:
            self.principal = self.principal_krw + c.convert('USD', 'KRW', self.principal_usd)
            self.value = self.principal
        
        else:
            self.principal = self.principal_krw + c.convert('USD', 'KRW', self.principal_usd)

            entry_agg = self.entries.aggregate(Sum('commission'), Avg('entry_risk'))
            opens_agg = self.entries.filter(is_open=True).aggregate(
                Sum('current_risk'), Sum('current_profit'))
            exits = FuturesExit.objects.filter(entry__account__id=self.id)
            
            current_profit = int(c.convert('USD','KRW', opens_agg['current_profit__sum'] or 0))
            self.risk = c.convert('USD','KRW', opens_agg['current_risk__sum'] or 0)
            self.commission = c.convert('USD','KRW', entry_agg['commission__sum'])
            self.avg_entry_risk = c.convert('USD','KRW', entry_agg['entry_risk__avg'])
            self.count = exits.count()
            if exits.count() > 0: 
                exit_agg = exits.aggregate(
                    Avg('duration'), Sum('profit'), Avg('profit'), StdDev('profit'))
                
                self.avg_profit = c.convert('USD','KRW', exit_agg['profit__avg'])
                self.duration = exit_agg['duration__avg']
                self.winning_rate = 100 * exits.filter(profit__gt=0).count()/exits.count()
                self.std = c.convert('USD','KRW', exit_agg['profit__stddev'])
                if exits.filter(profit__lte=0).count() > 0:
                    self.avg_ptr = abs(exits.filter(profit__gt=0).aggregate(Avg('profit'))['profit__avg']\
                            /exits.filter(profit__lte=0).aggregate(Avg('profit'))['profit__avg'])
                profit = c.convert('USD','KRW', exit_agg['profit__sum'])
            else:
                profit = 0
            self.value = self.principal + profit + current_profit - self.commission
            self.gross_profit = self.value - self.principal
        super(FuturesAccount, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}/{self.account_name}"

class  FuturesEntry(models.Model):
    POSITIONS = [
        (1, "Long"),
        (-1, "Short")
    ]
    account = models.ForeignKey(
                    FuturesAccount,
                    verbose_name="선물계좌",
                    related_name="entries",
                    on_delete=models.PROTECT)
    instrument = models.ForeignKey(
                    FuturesInstrument,
                    verbose_name="상품명",
                    on_delete=models.PROTECT)
    date = models.DateField("진입 날짜")
    code = models.CharField("종목코드", max_length=20)
    current_price = models.DecimalField("현재가", max_digits=12, decimal_places=6)
    position = models.SmallIntegerField("포지션", choices=POSITIONS)
    num_cons = models.SmallIntegerField("진입계약수")
    num_open_cons = models.SmallIntegerField("미청산계약수")
    num_close_cons = models.SmallIntegerField("청산계약수", default=0)
    
    entry_price = models.DecimalField("진입가", max_digits=12, decimal_places=6)
    stop_price = models.DecimalField("청산 예정가", max_digits=12, decimal_places=6)
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=2)
    current_profit = models.DecimalField("평가손익", max_digits=12, decimal_places=2, blank=True)
    entry_risk = models.DecimalField("진입 리스크", blank=True, max_digits=12, decimal_places=2)
    current_risk = models.DecimalField("현재 리스크", blank=True, max_digits=12, decimal_places=2)
    is_open = models.BooleanField("상태", default=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.entry_risk = ((self.entry_price - self.stop_price)*self.position/self.instrument.tickunit)\
                             *self.instrument.tickprice*self.num_cons
            
        if self.exits.count() > 0:
            self.num_close_cons = self.exits.aggregate(Sum('num_cons'))['num_cons__sum']
            self.num_open_cons = self.num_cons - self.num_close_cons
        self.current_risk = ((self.current_price - self.stop_price)*self.position/self.instrument.tickunit)\
                         *self.instrument.tickprice*self.num_open_cons
        self.current_profit = ((self.current_price - self.entry_price)*self.position/self.instrument.tickunit)\
                         *self.instrument.tickprice*self.num_open_cons
        self.is_open = True if self.num_open_cons > 0 else False
        super(FuturesEntry, self).save(*args, **kwargs)

    def __str__(self):
        return f"({self.id}) 상품: {self.instrument.name} / 날짜: {self.date}/ 리스크: {self.entry_risk}"
    class Meta:
        ordering = ('-id',)

class FuturesExit(models.Model):
    date = models.DateField("청산날짜")
    entry = models.ForeignKey(
               FuturesEntry,
               related_name="exits",
               verbose_name="진입매매",
               on_delete=models.CASCADE)
    num_cons = models.SmallIntegerField("청산계약수")
    price = models.DecimalField("청산가격", max_digits=12, decimal_places=6)
    profit = models.DecimalField("손익", blank=True, max_digits=9, decimal_places=2)
    duration = models.PositiveIntegerField("보유기간", blank=True)

    def save(self, *args, **kwargs):
        self.profit = ((self.price - self.entry.entry_price)*self.entry.position/self.entry.instrument.tickunit)\
                       * (self.entry.instrument.tickprice) * self.num_cons
        self.duration = (self.date - self.entry.date).days
        super(FuturesExit, self).save(*args, **kwargs)

    def __str__(self):
        return f"id = {self.id}, entry id = {self.entry.id}: {self.profit} / {self.date}"
    class Meta:
        ordering = ('-id',)

@receiver(post_save, sender=FuturesExit,
          dispatch_uid="update_entry_after_exit")
def update_entry_after_exit(sender, instance, **kwargs):
    instance.entry.save()

@receiver(post_save, sender=FuturesEntry,
          dispatch_uid="update_system_record")
def update_system_record(sender, instance, **kwargs):
    instance.account.save()
