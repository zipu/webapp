from django.contrib import admin

# Register your models here.
from asset.models import Cash, Stock, Futures

admin.site.register(Cash)
admin.site.register(Stock)
admin.site.register(Futures)