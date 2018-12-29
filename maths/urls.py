from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import DocumentView


urlpatterns = [
    path('', RedirectView.as_view(url='documents', permanent=False)),
    path('documents/', DocumentView.as_view(), name='documents')
]

