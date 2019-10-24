from django.contrib import admin

# Register your models here.
from trading.models import Instrument

admin.site.register(Instrument)