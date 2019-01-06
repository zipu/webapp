from django.db import models

# Create your models here.
from django.db import models
from django.db.models.signals import post_delete
from datetime import datetime

class KRW(models.Model):
    """ This class represents my korean won asset """

    date = models.DateField()
    cash = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Cash: {format(self.cash,',d')} WON | Stock: {format(self.stock,',d')} WON"

class CNY(models.Model):
    """ This class represents my chinese yuan asset """

    date = models.DateField()
    cash = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Cash: {format(self.cash,',d')} CNY | Stock: {format(self.stock,',d')} CNY"

class USD(models.Model):
    """ This class represents my usd asset """

    date = models.DateField()
    cash = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Cash: {format(self.cash,',d')}$ | Stock: {format(self.stock,',d')}$"


