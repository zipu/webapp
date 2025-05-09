from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import FuturesView, TransactionView, FuturesTradeView, FuturesStatView,\
      CalculatorView, CFTCView, OptionStrategyView
from .views import StockView, StockHistoryView
from .views import NoteView, KiwoomPositionView, LsApiTradeView

urlpatterns = [
    path('', RedirectView.as_view(url='futures', permanent=False)),
    path('futures/', FuturesView.as_view(), name='futures'),
    path('futures/statdata', FuturesStatView.as_view(), name='statdata'),
    path('futures/transaction/<int:page>', TransactionView.as_view(), name='transaction'),
    path('futures/trade/<int:page>', FuturesTradeView.as_view(), name='futurestrade'),
    path('futures/ls-api-trade', LsApiTradeView.as_view(), name='ls-api-trade'),
    path('futures/kiwoom-position', KiwoomPositionView.as_view(), name='kiwoom-position'),
    path('futures/calculator', CalculatorView.as_view(), name='calculator'),
    path('futures/cftc', CFTCView.as_view(), name='cftc'),
    path('futures/opstrat', OptionStrategyView.as_view(), name='opstrat'),
    path('note/<int:page>', NoteView.as_view(), name='note'),
    path('stock/', StockView.as_view(), name='stock'),
    path('stock/history/', StockHistoryView.as_view(), name='stockhistory'),
    #path('createrecord/', CreateRecordView.as_view(), name='record'),
    
    #path('updatecurrencyrates/', UpdateCurrencyRateView.as_view(), name='updatecurrencyrates')
]

