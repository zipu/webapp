from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView

from .views import AopsView

urlpatterns = [
    path('', RedirectView.as_view(url='1', permanent=False), name='index'),
    #path('', AopsView.as_view(), name='aops'),
    path('<int:page>/', AopsView.as_view(), name='aops'),
]

