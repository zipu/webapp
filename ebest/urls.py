from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView

from .views import EbestStockView

urlpatterns = [
    path('', RedirectView.as_view(url='stock', permanent=False)),
    path('stock/', EbestStockView.as_view(), name='stock'),
]

