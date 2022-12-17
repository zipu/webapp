from django.db import models

from django.db.models import Avg, Sum, Max, StdDev, F, ExpressionWrapper
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
from decimal import Decimal as D
from datetime import datetime, timedelta, time

#from forex_python.converter import CurrencyRates
import requests
from bs4 import BeautifulSoup

class CurrencyRates:
    """
    환율 계산 모듈
    """
    RATES = {
        'KRWUSD': 0,
        'KRWEUR': 0,
        'KRWCNY': 0,
        'KRWHKD': 0,
        'KRWJPY': 0
    }

    @classmethod
    def update(cls):
        url = 'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD,FRX.KRWEUR,FRX.KRWCNY,FRX.KRWHKD,FRX.KRWJPY'
        response = requests.get(url)

        if response.ok:
            rates = response.json()
            CurrencyRates.RATES = {
                'KRWUSD': D(str(rates[0]['basePrice'])),
                'KRWEUR': D(str(rates[1]['basePrice'])),
                'KRWCNY': D(str(rates[2]['basePrice'])),
                'KRWHKD': D(str(rates[3]['basePrice'])),
                'KRWJPY': D(str(rates[4]['basePrice']))
            }
            return CurrencyRates.RATES
            
        else:
            #print(f"환율정보 갱신 실패: {base}/{target}")
            raise ValueError(f"환율정보 갱신 실패")

    def convert(self, base, target, amount):
        if base == target: 
            return amount
            
        converted = amount * CurrencyRates.RATES[f'{target}{base}']
        return converted




def convert_to_decimal(value, system):
    "8진법 또는 32진법으로 들어오는 가격을 10진법으로 변환"
    a,b = [float(i) for i in value.split("'")]
    return a+b/system

def create_record(account):
    now = datetime.now()
    if account=='all':
        create_record('cash')
        create_record('stock')
        create_record('futures')
        create_record('asset')

    if account=='asset':
        stock = StockAccount.objects.all().first()
        cash = CashAccount.objects.all().latest('date','id')
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
        acc = CashAccount.objects.all().latest('date','id')
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
        
        # 시스템 통합 정보 갱신
        accounts = FuturesAccount.objects.all()
        agg = accounts.aggregate(
            Sum('principal'),
            Sum('value'),
            Sum('risk')
            )
        Record(
            date=now,
            account_symbol='FA', #total futures asset
            principal=agg['principal__sum'],
            value=agg['value__sum'],
            risk=agg['risk__sum']
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
        self.rate_profit =  self.gross_profit/self.principal * 100 if self.principal > 0 else 0
        

        if self.value > 0:
            self.rate_risk = self.risk/self.value * 100
        else:
            self.rate_risk = 0
        
        if not self.id:
            records = Record.objects.filter(account_symbol=self.account_symbol).all()
        else:
            records = Record.objects.filter(account_symbol=self.account_symbol, id__lt=self.id).all()
        
        if records.count():
            last_gross_profit = records.latest('date').gross_profit
            #last_principal = records.latest('date').principal
            last_mdd = records.latest('date').mdd
            last_max = records.aggregate(Max('value'))['value__max']
            
            self.avg_risk = records.aggregate(Avg('risk'))['risk__avg']
            
            
            self.volatility_day = 100*abs(last_gross_profit-self.gross_profit)\
                                /(last_gross_profit+self.principal) if last_gross_profit+self.principal > 0 else 0
            since = self.date - timedelta(days=30)
            self.volatility = (records.filter(date__gte=since).all()\
                            .aggregate(Avg('volatility_day'))['volatility_day__avg'] or 0)
            
            max_value = max(last_max, self.value)
            self.drawdown = 100 * (max_value - self.value)/max_value if max_value > 0 else 0
            self.mdd = max(self.drawdown, last_mdd)

            #계좌오픈일 찾기
            if self.account_symbol == 'A':
                first_date = CashAccount.objects.all().earliest('date').date
            elif self.account_symbol == 'C':
                first_date = CashAccount.objects.all().earliest('date').date
            elif self.account_symbol == 'S':
                first_date = StockAccount.objects.first().date
            elif self.account_symbol == 'FA': #(선물통합)
                first_date = FuturesAccount.objects.all().earliest('date').date

            else:
                first_date = FuturesAccount.objects.get(symbol=self.account_symbol).date

            days = (self.date.date() - first_date).days
            if (days > 1) and (self.principal > 0) and (self.value > 0):
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

    NUMBER_SYSTEMS = [
        (10, '10진법'),
        (8, '8진법'),
        (32, '32진법')
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
    number_system = models.SmallIntegerField("진법", choices=NUMBER_SYSTEMS, default=10)
    current_price = models.DecimalField("현재가", max_digits=12, decimal_places=6, null=True, blank=True)
    opentime = models.TimeField("거래 시작시간") #장 시작시간(한국)
    closetime = models.TimeField("거래 종료시간") #장 종료시간(한국)

    def calc_value(self, entry_price, exit_price, num_cons, position):
        # 가격 차이를 돈 가치로 변환
        return position * (exit_price-entry_price)*num_cons*self.tickprice/self.tickunit

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    class Meta:
        ordering = ('name',)

class FuturesAccount2:
    asset = models.ForeignKey(
        Asset,
        related_name="futures",
        verbose_name="자산종류",
        on_delete=models.CASCADE)
    date = models.DateField("날짜")
    account_name = models.CharField("계좌명", max_length=20, default='futures')
    symbol = models.CharField("계좌코드", max_length=16, default='F')
    
    principal_krw = models.DecimalField("시드(원)", max_digits=12, decimal_places=0)
    pricnipal_usd = models.DecimalField("시드(달러)", max_digits=12, decimal_places=1)
    principal = models.DecimalField("총시드(원)",blank=True, max_digits=12, decimal_places=0)

    def save(self, *args, **kwargs):
        c = CurrencyRates()
        self.principal = c.convert('USD','KRW',self.usd)+\
                c.convert('CNY','KRW',self.cny)+\
                self.krw
        
        super(FuturesAccount, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"({self.account_name}){self.total} won - {self.date}"

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
    principal_usd = models.DecimalField("투자원금(USD)", max_digits=11, decimal_places=2)
    principal_eur = models.DecimalField("투자원금(EUR)", max_digits=11, decimal_places=2,  default=0)
    
    value_usd = models.DecimalField("달러자산가치(USD)", max_digits=11, decimal_places=2, default=0)
    value_eur = models.DecimalField("유로자산가치(EUR)", max_digits=11, decimal_places=2,  default=0)
    value = models.DecimalField("총자산가치", max_digits=12, decimal_places=0, blank=True)
    gross_profit = models.DecimalField("누적수익", max_digits=12, decimal_places=0, blank=True)
    commission = models.DecimalField("수수료", max_digits=9, decimal_places=0, blank=True)
    avg_ptr = models.FloatField("평균손익비", blank=True)
    winning_rate = models.FloatField("승률", blank=True)
    avg_profit = models.DecimalField("평균수익", max_digits=12, decimal_places=0, blank=True)
    #std = models.DecimalField("수익표준편차", max_digits=12, decimal_places=0, blank=True)
    duration = models.PositiveIntegerField("평균보유기간", blank=True)
    avg_entry_risk = models.DecimalField("평균진입리스크", max_digits=12, decimal_places=0, blank=True)
    risk = models.DecimalField("현재총리스크", max_digits=12, decimal_places=0, blank=True)
    count = models.PositiveIntegerField("매매횟수", default=0)

    def save(self, *args, **kwargs):
        c = CurrencyRates()
        if not self.id:
            self.principal = self.principal_krw\
                             + c.convert('USD', 'KRW', self.principal_usd)\
                             + c.convert('EUR', 'KRW', self.principal_eur)
            self.value = self.principal
        
        else:
            self.principal = self.principal_krw\
                             + c.convert('USD', 'KRW', self.principal_usd)\
                             + c.convert('EUR', 'KRW', self.principal_eur)

            usd_entry_agg = self.entries.filter(instrument__currency='USD').aggregate(Sum('commission'), Sum('entry_risk'))
            eur_entry_agg = self.entries.filter(instrument__currency='EUR').aggregate(Sum('commission'), Sum('entry_risk'))
            exits = FuturesExit.objects.filter(entry__account__id=self.id)
            
            usd_opens_agg = self.entries.filter(is_open=True).filter(instrument__currency='USD').aggregate(
                Sum('current_risk'), Sum('current_profit'))
            usd_exits = exits.filter(entry__instrument__currency='USD')

            eur_opens_agg = self.entries.filter(is_open=True).filter(instrument__currency='EUR').aggregate(
                Sum('current_risk'), Sum('current_profit'))
            eur_exits = exits.filter(entry__instrument__currency='EUR')
            
            
            current_profit = int(c.convert('USD','KRW', usd_opens_agg['current_profit__sum'] or 0))\
                            + int(c.convert('EUR','KRW', eur_opens_agg['current_profit__sum'] or 0))
            self.risk = int(c.convert('USD','KRW', usd_opens_agg['current_risk__sum'] or 0))\
                        + int(c.convert('EUR','KRW', eur_opens_agg['current_risk__sum'] or 0))\
            
            #self.commission = c.convert('USD','KRW', entry_agg['commission__sum'])
            self.avg_entry_risk = (int(c.convert('USD','KRW', usd_entry_agg['entry_risk__sum'] or 0))\
                                   +int(c.convert('EUR','KRW', eur_entry_agg['entry_risk__sum'] or 0)))\
                                   / self.entries.count() if self.entries.count() else 0
            
            self.count = self.entries.count()
            if exits.count() > 0: 
                usd_exit_agg = usd_exits.aggregate(Sum('profit'), Sum('commission'))
                eur_exit_agg = eur_exits.aggregate(Sum('profit'), Sum('commission'))
                
                self.avg_profit = (int(c.convert('USD','KRW', usd_exit_agg['profit__sum'] or 0))\
                                    + int(c.convert('EUR','KRW', eur_exit_agg['profit__sum'] or 0)))\
                                    / exits.count()
                                
                self.duration = exits.aggregate(Avg('duration'))['duration__avg']
                self.winning_rate = 100 * exits.filter(profit__gt=0).count()/exits.count()
                #self.std = c.convert('USD','KRW', exit_agg['profit__stddev'])
                # 평균손익비 계산
                if exits.filter(profit__lte=0).count() > 0:
                    sum_wins_usd = int(c.convert('USD', 'KRW', usd_exits.filter(profit__gt=0).aggregate(Sum('profit'))['profit__sum'] or 0))
                    sum_wins_eur = int(c.convert('EUR', 'KRW', eur_exits.filter(profit__gt=0).aggregate(Sum('profit'))['profit__sum'] or 0))
                    sum_loses_usd = int(c.convert('USD', 'KRW', usd_exits.filter(profit__lte=0).aggregate(Sum('profit'))['profit__sum'] or 0))
                    sum_loses_eur = int(c.convert('EUR', 'KRW', eur_exits.filter(profit__lte=0).aggregate(Sum('profit'))['profit__sum'] or 0))
                    avg_wins = (sum_wins_usd + sum_wins_eur)/exits.filter(profit__gt=0).count() if exits.filter(profit__gt=0).count() > 0 else 0
                    avg_loses = (sum_loses_usd + sum_loses_eur)/exits.filter(profit__lte=0).count() if exits.filter(profit__lte=0).count() > 0 else 0
                    self.avg_ptr = abs(avg_wins/avg_loses) if avg_loses >0 else 0
                profit = int(c.convert('USD','KRW', usd_exit_agg['profit__sum'] or 0))\
                        + int(c.convert('EUR','KRW', eur_exit_agg['profit__sum'] or 0))
                
                usd_commission = int(c.convert('USD','KRW', usd_entry_agg['commission__sum'] or 0))\
                                + int(c.convert('USD','KRW', usd_exit_agg['commission__sum'] or 0))

                eur_commission =  int(c.convert('EUR','KRW', eur_entry_agg['commission__sum'] or 0))\
                                + int(c.convert('EUR','KRW', eur_exit_agg['commission__sum'] or 0))

                self.commission = usd_commission + eur_commission
                self.value = self.principal + profit + current_profit - self.commission
                self.value_usd = self.principal_usd + (usd_opens_agg['current_profit__sum'] or 0)\
                                + ( usd_exit_agg['profit__sum'] or 0 ) - (usd_entry_agg['commission__sum'] or 0) - (usd_exit_agg['commission__sum'] or 0)
                self.value_eur = self.principal_eur + (eur_opens_agg['current_profit__sum'] or 0)\
                                + ( eur_exit_agg['profit__sum'] or 0 ) - (eur_entry_agg['commission__sum'] or 0) - (eur_exit_agg['commission__sum'] or 0)
                self.gross_profit = self.value - self.principal
            else:
                profit = 0
                usd_commission = int(c.convert('USD','KRW', usd_entry_agg['commission__sum'] or 0))

                eur_commission =  int(c.convert('EUR','KRW', eur_entry_agg['commission__sum'] or 0))

                self.commission = usd_commission + eur_commission
                self.value = self.principal + profit + current_profit - self.commission
                self.value_usd = self.principal_usd + (usd_opens_agg['current_profit__sum'] or 0)\
                               - (usd_entry_agg['commission__sum'] or 0)
                self.value_eur = self.principal_eur + (eur_opens_agg['current_profit__sum'] or 0)\
                               - (eur_entry_agg['commission__sum'] or 0)
                self.gross_profit = self.value - self.principal
        super(FuturesAccount, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.account_name}"

class FuturesStrategy(models.Model):
    name = models.CharField("전략명", max_length=50)
    code = models.CharField("전략코드", max_length=10)
    description = models.TextField("설명", null=True, blank=True)

    def __str__(self):
        return f"{self.name}/{self.code}"

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

    strategy = models.ForeignKey(
               FuturesStrategy,
               blank=True,
               null=True,
               related_name="strategies",
               verbose_name="전략",
               on_delete=models.CASCADE)
    
    date = models.DateField("진입 날짜")
    code = models.CharField("종목코드", max_length=20)
    expiration = models.DateField("만기일", null=True)
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
        c = CurrencyRates()
        if not self.id:
            entry_risk = ((self.entry_price - self.stop_price)*self.position/self.instrument.tickunit)\
                             *self.instrument.tickprice*self.num_cons
            
            self.entry_risk = self.current_risk = c.convert(self.instrument.currency, 'USD', entry_risk)
            
        if self.id and self.exits.count() > 0:
            self.num_close_cons = self.exits.aggregate(Sum('num_cons'))['num_cons__sum']
            self.num_open_cons = self.num_cons - self.num_close_cons
        current_risk = ((self.current_price - self.stop_price)*self.position/self.instrument.tickunit)\
                         *self.instrument.tickprice*self.num_open_cons
        self.current_risk = c.convert(self.instrument.currency, 'USD', current_risk)
        current_profit = ((self.current_price - self.entry_price)*self.position/self.instrument.tickunit)\
                         *self.instrument.tickprice*self.num_open_cons
        self.current_profit = c.convert(self.instrument.currency, 'USD', current_profit)
        self.is_open = True if self.num_open_cons > 0 else False
        super(FuturesEntry, self).save(*args, **kwargs)

    def __str__(self):
        return f"({self.account.account_name}) {self.id}/{self.instrument.name}/{self.entry_price:.{self.instrument.decimal_places}f}/ r:{self.current_risk:.0f}/ ct:{self.num_open_cons}/{self.num_cons}"
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
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=2, default=0)
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

class FuturesRecord(models.Model):
    """
    해선 계좌의 통계 기록
    """
    date = models.DateTimeField("날짜")
    
    principal = models.DecimalField("총시드(원)", max_digits=12, decimal_places=0, blank=True)
    principal_krw = models.DecimalField("시드(원)", max_digits=12, decimal_places=0, blank=True)
    principal_usd = models.DecimalField("시드(달러)", max_digits=12, decimal_places=1, blank=True)

    # 총가치: 시드 + 평가 + 실현 손익을 합산하여 원화로 계산
    value = models.DecimalField("총자산", max_digits=12, decimal_places=0, blank=True)
    value_usd = models.DecimalField("자산(달러)", max_digits=12, decimal_places=0, blank=True)
    commission = models.DecimalField("수수료", max_digits=9, decimal_places=0, blank=True)

    # 손익
    gross_profit = models.DecimalField("누적수익", max_digits=12, decimal_places=0, blank=True)
    #paper_profit = 

    #averge_profit
    #average_ptr
    #winning_rate

    #cagr


class Transaction(models.Model):
    POSITIONS = [
        (1, "Long"),
        (-1, "Short")
    ]
    instrument = models.ForeignKey(
                    FuturesInstrument,
                    verbose_name="상품",
                    on_delete=models.PROTECT)

    ebest_id = models.PositiveSmallIntegerField("이베스트 체결번호")
    ebest_code = models.CharField("이베스트 상품코드", max_length=20)
    date = models.DateTimeField("체결날짜")
    position = models.SmallIntegerField("포지션", choices=POSITIONS)
    price = models.DecimalField("진입가", max_digits=12, decimal_places=6)
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=2)
    
    trade = models.ForeignKey(
        "FuturesTrade",
        models.SET_NULL,
        verbose_name="거래",
        related_name="transactions",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"({self.id}/{self.ebest_id} ){self.date}/{self.instrument.name}/{self.position}"
    


class FuturesTrade(models.Model):
    POSITIONS = [
        (1, "Long"),
        (-1, "Short")
    ]

    instrument = models.ForeignKey(
                    FuturesInstrument,
                    verbose_name="상품",
                    on_delete=models.PROTECT)

    strategy = models.ForeignKey(
                    FuturesStrategy,
                    related_name='trades',
                    verbose_name="전략",
                    on_delete=models.PROTECT,
                    null=True, blank=True)

    
    pub_date = models.DateTimeField("시작날짜")
    end_date = models.DateTimeField("종료날짜", null=True, blank=True)
    ebest_code = models.CharField("이베스트 상품코드", max_length=20)
    position = models.SmallIntegerField("포지션", choices=POSITIONS)
    current_price = models.DecimalField(
                    "현재가", max_digits=12, decimal_places=6,
                    null=True, blank=True)

    avg_entry_price = models.DecimalField(
                    "평균진입가", max_digits=12, decimal_places=6,
                    null=True, blank=True) 

    avg_exit_price = models.DecimalField(
                    "평균청산가", max_digits=12, decimal_places=6,
                    null=True, blank=True)

    stop_price = models.DecimalField(
        "손절가", max_digits=12, decimal_places=6,
        null=True, blank=True)

    num_entry_cons = models.SmallIntegerField("총진입계약수", default=0)
    num_exit_cons = models.SmallIntegerField("총청산계약수", default=0, null=True, blank=True)
    
    risk = models.DecimalField("리스크", max_digits=12, decimal_places=2, default=0)
    paper_profit = models.DecimalField("평가손익", max_digits=12, decimal_places=2, default=0)
    realized_profit = models.DecimalField("실현손익", max_digits=12, decimal_places=2, default=0)
    commission = models.DecimalField("수수료", max_digits=6, decimal_places=2, default=0)

    is_open = models.BooleanField("상태", default=True)
    description = models.TextField("설명", null=True, blank=True)

    @staticmethod
    def add_transactions():
        """
        transaction(체결기록)가 기존 거래와 관련된 체결이면 기존 거래에 추가하고
        그렇지 않으면 신규 거래를 생성
        views/TransactionView/post 에서 사용함
        """
        transactions = Transaction.objects.filter(trade=None).order_by('date')
        for transaction in transactions:
            trades = FuturesTrade.objects.filter(ebest_code = transaction.ebest_code, is_open=True)
            # 해당 transaction의 상품코드와 같은 열려있는 거래가 없으면 생성
            if not trades:
                trade = FuturesTrade(
                    instrument = transaction.instrument,
                    pub_date = transaction.date,
                    ebest_code = transaction.ebest_code,
                    position = transaction.position,
                )
                trade.save()
            # 기존 거래가 있으면 transaction을 추가
            else:
                trade = trades[0]
                
            trade.transactions.add(transaction)
            trade.update()
    
    def update(self):
        # 매매내역 갱신. 손익 등 정보 갱신
            
        entries = self.transactions.filter(position = self.position).order_by('date')
        exits = self.transactions.filter(position = self.position*-1).order_by('date')
        matches = [(entries[i], exits[i]) for i in range(exits.count()) ]

        
        self.commission = self.transactions.all().aggregate(Sum('commission'))['commission__sum']
               
        
        self.num_entry_cons = entries.count()
        self.num_exit_cons = exits.count()
        if self.num_entry_cons < self.num_exit_cons:
            raise ValueError("청산 계약수가 진입 계약수를 초과")
        
        elif self.num_entry_cons == self.num_exit_cons:
            self.end_date = exits.reverse()[0].date
            self.is_open = False
        
        self.avg_entry_price = entries.aggregate(Avg('price'))['price__avg']
        self.avg_exit_price = exits.aggregate(Avg('price'))['price__avg']

        # 실현 손익 계산
        self.realized_profit = 0
        for match in matches:
            self.realized_profit += self.instrument.calc_value(
                match[0].price, match[1].price, 1, self.position
            ) 
            
        #평가 손익 계산
        if self.current_price:
            self.paper_profit = self.instrument.calc_value(
                self.avg_entry_price, self.current_price, 
                self.num_entry_cons - self.num_exit_cons, self.position
            )
        # 리스크 계산
        if self.stop_price:
            self.risk = self.instrument.calc_value(
                self.avg_entry_price, self.stop_price,
                self.num_entry_cons - self.num_exit_cons, self.position
            )

        self.save()


    def __str__(self):
        return f"({self.id}/{self.pub_date}/{self.instrument.name}/{self.realized_profit}"    








@receiver(post_save, sender=FuturesExit,
          dispatch_uid="update_entry_after_exit")
def update_entry_after_exit(sender, instance, **kwargs):
    instance.entry.save()

@receiver(post_save, sender=FuturesEntry,
          dispatch_uid="update_system_record")
def update_system_record(sender, instance, **kwargs):
    instance.account.save()


###########################################
# 자금 이체                                #
###########################################
class Transfer(models.Model):
    ACCOUNTS = [
        ("N", "없음"),
        ("C", "현금"),
        ("S", "주식"),
        ("F", "선물")
    ] 
    
    CURRENCIES = [
        ('KRW', '원'),
        ('USD', '달러'),
        ('CNY', '위안'),
        ('EUR', '유로')
    ]
    
    date = models.DateField("날짜")
    acc_from = models.CharField("출금계좌", choices=ACCOUNTS, max_length=10)
    currency_from = models.CharField("출금통화", choices=CURRENCIES, max_length=10, blank=True, null=True)
    amount_from = models.DecimalField("출금액", max_digits=15, decimal_places=2, blank=True, null=True)
    acc_to = models.CharField("입금계좌", choices=ACCOUNTS, max_length=10)
    currency_to = models.CharField("입금통화", choices=CURRENCIES, max_length=10)
    amount_to = models.DecimalField("입금액", max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.acc_from == "C":
            latest_acc = CashAccount.objects.latest('date')
            acc = CashAccount(
                asset=latest_acc.asset,
                date=datetime.now().date(),
                symbol='C'
            )
            acc.krw = latest_acc.krw - self.amount_from if self.currency_from == 'KRW' else latest_acc.krw
            acc.cny = latest_acc.cny - self.amount_from if self.currency_from == 'CNY' else latest_acc.cny
            acc.usd = latest_acc.usd - self.amount_from if self.currency_from == 'USD' else latest_acc.usd
            acc.save()
        
        
        elif self.acc_from == "S":
            acc = StockAccount.objects.get(symbol=self.acc_from)
            acc.principal = acc.principal - self.amount_from
            acc.save()

        elif self.acc_from == "F":
            acc = FuturesAccount.objects.latest('date')
            if self.currency_from == 'KRW':
                acc.principal_krw = acc.principal_krw - self.amount_from
            elif self.currency_from == 'USD':
                acc.principal_usd = acc.principal_usd - self.amount_from
            #elif self.currency_from == 'EUR':
            #    acc.principal_eur = acc.principal_eur - self.amount_from
            acc.save()

        
        if self.acc_to == "C":
            latest_acc = CashAccount.objects.latest('date')
            acc = CashAccount(
                asset=latest_acc.asset,
                date=datetime.now().date(),
                symbol='C'
            )
            acc.krw = latest_acc.krw + self.amount_to if self.currency_to == 'KRW' else latest_acc.krw
            acc.cny = latest_acc.cny + self.amount_to if self.currency_to == 'CNY' else latest_acc.cny
            acc.usd = latest_acc.usd + self.amount_to if self.currency_to == 'USD' else latest_acc.usd
            acc.save()

        elif self.acc_to == "S":
            acc = StockAccount.objects.get(symbol=self.acc_to)
            acc.principal = acc.principal + self.amount_to
            acc.save()

        elif self.acc_to == "F":
            acc = FuturesAccount.objects.latest('date')
            if self.currency_to == 'KRW':
                acc.principal_krw = acc.principal_krw + self.amount_to
            elif self.currency_to == 'USD':
                acc.principal_usd = acc.principal_usd + self.amount_to
            #elif self.currency_to == 'EUR':
            #    acc.principal_eur = acc.principal_eur + self.amount_to
            acc.save()
        
        super(Transfer, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"({self.acc_from} --> {self.acc_to}) 출금: {self.amount_from},  입금: {self.amount_to}"

