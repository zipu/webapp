from django.db import models

# Create your models here.
from django.db import models
from django.db.models.signals import post_delete
from datetime import datetime

from forex_python.converter import CurrencyRates

class Cash(models.Model):

    date = models.DateField()
    krw = models.IntegerField(null=True, blank=True)
    cny = models.IntegerField(null=True, blank=True)
    usd = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if Cash.objects.count():
            last = Cash.objects.latest('id')
        
        if self.krw is None:
            self.krw = last.krw

        if self.cny is None:
            self.cny = last.cny

        if self.usd is None:
            self.usd = last.usd

        c = CurrencyRates()
        self.total = c.convert('USD','KRW',self.usd)+\
                     c.convert('CNY','KRW',self.cny)+\
                     self.krw

        super(Cash, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.total} won - {self.date}"
    
    class Meta:
        verbose_name_plural = 'Cash'



class Stock(models.Model):
    date = models.DateField()
    stocks = models.IntegerField(null=True, blank=True)
    etfs = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if Stock.objects.count():
            last = Stock.objects.latest('id')
        
        if self.stocks is None:
            self.stocks = last.stocks if last.stocks else 0

        if self.etfs is None:
            self.etfs = last.etfs if last.etfs else 0

        self.total = self.stocks + self.etfs

        super(Stock, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.total:,} won - {self.date}"

    class Meta:
        verbose_name_plural = 'Equities'

class Futures(models.Model):
    date = models.DateField()
    futures_in_krw = models.IntegerField(null=True, blank=True)
    futures_in_usd = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if Futures.objects.count():
            last = Futures.objects.latest('id')
        
        if self.futures_in_krw is None:
            self.futures_in_krw = last.futures_in_krw if last.futures_in_krw else 0 

        if self.futures_in_usd is None:
            self.futures_in_usd = last.futures_in_usd if last.futures_in_usd else 0

        c = CurrencyRates()
        self.total = c.convert('USD','KRW',self.futures_in_usd) +\
                     self.futures_in_krw

        super(Futures, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Derivative'

    def __str__(self):
        return f"{self.total:,} - {self.date}"