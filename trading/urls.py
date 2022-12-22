from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import FuturesView, TransactionView, FuturesTradeView, FuturesStatView
from .views import StockView, StockHistoryView
from .views import UpdateView

urlpatterns = [
    path('', RedirectView.as_view(url='futures', permanent=False)),
    path('futures/', FuturesView.as_view(), name='futures'),
    path('futures/statdata', FuturesStatView.as_view(), name='statdata'),
    path('futures/transaction/<int:page>', TransactionView.as_view(), name='transaction'),
    path('futures/trade/<int:page>', FuturesTradeView.as_view(), name='futurestrade'),
    path('stock/', StockView.as_view(), name='stock'),
    path('stock/history/', StockHistoryView.as_view(), name='stockhistory'),
    path('update/', UpdateView.as_view(), name='update'),
    #path('createrecord/', CreateRecordView.as_view(), name='record'),
    
    #path('updatecurrencyrates/', UpdateCurrencyRateView.as_view(), name='updatecurrencyrates')
]

