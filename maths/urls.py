from django.urls import path, include
from django.contrib import admin
from .views import IndexView


urlpatterns = [
    path('', IndexView.as_view(), name='index')
]

