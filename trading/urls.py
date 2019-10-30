from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import FuturesView, FuturesHistoryView, FuturesChartView

urlpatterns = [
    path('', RedirectView.as_view(url='futures/1', permanent=False)),
    path('futures/<int:system>', FuturesView.as_view(), name='futures'),
    path('futures/<int:system>/history', FuturesHistoryView.as_view(), name='futureshistory'),
    path('futures/<int:system>/chartdata', FuturesChartView.as_view(), name='futureschart')
]

