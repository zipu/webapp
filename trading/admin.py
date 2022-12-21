from django.contrib import admin

# Register your models here.
from trading.models import FuturesAccount, FuturesInstrument, FuturesStrategy, Transaction, FuturesTrade, Tags
from trading.models import Record, CashAccount, Asset
from trading.models import StockAccount, StockBuy, StockSell, StockTradeUnit
from trading.models import Transfer, Currency

admin.site.register(
 [FuturesAccount, FuturesStrategy, Transaction, FuturesTrade, Tags, Currency])
admin.site.register(
 [Record, CashAccount, Asset]
)
admin.site.register(
 [StockAccount, StockBuy, StockSell, StockTradeUnit]
)
admin.site.register(
 [Transfer]
)

@admin.register(FuturesInstrument)
class FuturesInstrumentAdmin(admin.ModelAdmin):
    search_fields = ["name", "symbol", "exchange"]



#admin.site.register(System)
#admin.site.register(FuturesEntry)
#admin.site.register(FuturesExit)l