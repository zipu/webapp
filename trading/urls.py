from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import RecordsView, RecordsListView, ChartView

urlpatterns = [
    path('', RedirectView.as_view(url='records', permanent=False)),
    path('records/', RecordsView.as_view(), name='records'),
    path('records/details/', RecordsListView.as_view(), name='recordsdetail'),
    path('records/chart/<int:pk>', ChartView.as_view(), name='chart')
]

