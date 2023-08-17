from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView

from .views import EbestStockView, CFTCView

urlpatterns = [
    path('', RedirectView.as_view(url='cftc', permanent=False)),
    path('stock/', EbestStockView.as_view(), name='stock'),
    path('cftc/', CFTCView.as_view(), name='cftc'),
]

