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
        return f"You have {self.total} won at {self.date}"

