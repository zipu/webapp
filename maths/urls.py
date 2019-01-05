from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import DocumentView, KlassView, KlassDetailView


urlpatterns = [
    path('', RedirectView.as_view(url='document', permanent=False)),
    path('document/', DocumentView.as_view(), name='document'),
    path('klass/', KlassView.as_view(), name='klass'),
    path('klass/<int:pk>', KlassDetailView.as_view(), name='klassdetail')
]

