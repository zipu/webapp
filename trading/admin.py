from django.contrib import admin

# Register your models here.
from trading.models import Instrument, FuturesSystem, FuturesEntry, FuturesExit

admin.site.register(
 [Instrument, FuturesSystem, FuturesEntry, FuturesExit]
)
#admin.site.register(System)
#admin.site.register(FuturesEntry)
#admin.site.register(FuturesExit)l