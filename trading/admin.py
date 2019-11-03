from django.contrib import admin

# Register your models here.
from trading.models import Instrument, FuturesSystem, FuturesEntry, FuturesExit, FuturesTrackRecord
from trading.models import StockSummary, StockStatement, StockBuy, StockSell

admin.site.register(
 [Instrument, FuturesSystem, FuturesEntry, FuturesExit,FuturesTrackRecord]
)
admin.site.register(
 [StockSummary, StockStatement, StockBuy, StockSell]
)
#admin.site.register(System)
#admin.site.register(FuturesEntry)
#admin.site.register(FuturesExit)l