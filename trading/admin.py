from django.contrib import admin

# Register your models here.
from trading.models import FuturesInstrument, FuturesAccount, FuturesEntry, FuturesExit, FuturesStrategy, Transaction
from trading.models import Record, CashAccount, Asset
from trading.models import StockAccount, StockBuy, StockSell, StockTradeUnit
from trading.models import Transfer

admin.site.register(
 [FuturesAccount, FuturesStrategy, Transaction])
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


@admin.register(FuturesExit)
class FuturesExitAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(FuturesExitAdmin, self).get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['entry'].initial = obj.entry
            form.base_fields['entry'].queryset = FuturesEntry.objects
        else:
            form.base_fields['entry'].queryset = FuturesEntry.objects.filter(is_open=True)
        return form

#admin.site.register(System)
#admin.site.register(FuturesEntry)
#admin.site.register(FuturesExit)l