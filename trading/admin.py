from django.contrib import admin

# Register your models here.
from trading.models import FuturesInstrument, FuturesAccount, FuturesEntry, FuturesExit
from trading.models import Record, CashAccount, Asset
from trading.models import StockAccount, StockBuy, StockSell, StockTradeUnit

admin.site.register(
 [FuturesInstrument, FuturesAccount, FuturesEntry, FuturesExit])
admin.site.register(
 [Record, CashAccount, Asset]
)
admin.site.register(
 [StockAccount, StockBuy, StockSell, StockTradeUnit]
)

#admin.site.register(System)
#admin.site.register(FuturesEntry)
#admin.site.register(FuturesExit)l