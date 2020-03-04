from django.contrib import admin

# Register your models here.
from trading.models import FuturesInstrument, FuturesAccount, FuturesEntry, FuturesExit
from trading.models import Record, CashAccount, Asset
from trading.models import StockAccount, StockBuy, StockSell, StockTradeUnit
from trading.models import Transfer

admin.site.register(
 [FuturesAccount, FuturesExit])
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

@admin.register(FuturesEntry)
class FuturesEntryAdmin(admin.ModelAdmin):
    autocomplete_fields = ["instrument"]

#admin.site.register(System)
#admin.site.register(FuturesEntry)
#admin.site.register(FuturesExit)l