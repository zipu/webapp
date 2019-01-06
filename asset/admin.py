from django.contrib import admin

# Register your models here.
from asset.models import KRW, CNY, USD

admin.site.register(KRW)
admin.site.register(CNY)
admin.site.register(USD)