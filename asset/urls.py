from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import AssetView


urlpatterns = [
    path('', AssetView.as_view(), name='asset'),
]

