from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import FuturesView, FuturesHistoryView, FuturesChartView
from .views import StockView, StockHistoryView, StockChartView

urlpatterns = [
    path('', RedirectView.as_view(url='futures/1', permanent=False)),
    path('futures/<int:system>', FuturesView.as_view(), name='futures'),
    path('futures/<int:system>/history', FuturesHistoryView.as_view(), name='futureshistory'),
    path('futures/<int:system>/chartdata', FuturesChartView.as_view(), name='futureschart'),
    path('stock/', StockView.as_view(), name='stock'),
    path('stock/history', StockHistoryView.as_view(), name='stockhistory'),
    path('stock/chartdata', StockChartView.as_view(), name='stockchart'),
]

