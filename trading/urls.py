from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import FuturesView, FuturesHistoryView, TransactionView, FuturesTradeView, FuturesStatView
from .views import StockView, StockHistoryView
from .views import CashView, AssetView, ChartView, StatView
from .views import UpdateView, ReportView, CreateRecordView, UpdateCurrencyRateView

urlpatterns = [
    path('', RedirectView.as_view(url='asset', permanent=False)),
    path('asset/', AssetView.as_view(), name='asset'),
    path('futures/stat', FuturesView.as_view(), name='futures'),
    path('futures/statdata', FuturesStatView.as_view(), name='statdata'),
    path('futures/transaction/<int:page>', TransactionView.as_view(), name='transaction'),
    path('futures/trade/<int:page>', FuturesTradeView.as_view(), name='futurestrade'),
    path('futures/<int:system>/history/', FuturesHistoryView.as_view(), name='futureshistory'),
    path('stock/', StockView.as_view(), name='stock'),
    path('stock/history/', StockHistoryView.as_view(), name='stockhistory'),
    path('cash/', CashView.as_view(), name='cash'),
    path('chart/<str:account>/', ChartView.as_view(), name='chart'),
    path('update/', UpdateView.as_view(), name='update'),
    path('report/', ReportView.as_view(), name='report'),
    path('createrecord/', CreateRecordView.as_view(), name='record'),
    path('stat/<int:account>/', StatView.as_view(), name='stat')
    
    #path('updatecurrencyrates/', UpdateCurrencyRateView.as_view(), name='updatecurrencyrates')
]

