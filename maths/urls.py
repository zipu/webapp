from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from .views import MathsView


urlpatterns = [
    path('', login_required(MathsView.as_view()), name='math_index')
]

