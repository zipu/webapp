from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import RecordView

urlpatterns = [
    path('', RedirectView.as_view(url='records', permanent=False)),
    path('records/', RecordView.as_view(), name='records'),
]

