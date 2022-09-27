from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import FuturesView, FuturesHistoryView
from .views import StockView, StockHistoryView
from .views import CashView, AssetView, ChartView
from .views import UpdatePriceView, ReportView, CreateRecordView

urlpatterns = [
    path('', RedirectView.as_view(url='asset', permanent=False)),
    path('asset', AssetView.as_view(), name='asset'),
    path('futures/<int:system>', FuturesView.as_view(), name='futures'),
    path('futures/<int:system>/history', FuturesHistoryView.as_view(), name='futureshistory'),
    path('stock', StockView.as_view(), name='stock'),
    path('stock/history', StockHistoryView.as_view(), name='stockhistory'),
    path('cash', CashView.as_view(), name='cash'),
    path('chart/<str:account>', ChartView.as_view(), name='chart'),
    path('update', UpdatePriceView.as_view(), name='updateprice'),
    path('report', ReportView.as_view(), name='report'),
    path('createrecord', CreateRecordView.as_view(), name='record')
]

