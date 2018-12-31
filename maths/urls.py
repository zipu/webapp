from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import DocumentView, CourseView


urlpatterns = [
    path('', RedirectView.as_view(url='document', permanent=False)),
    path('document/', DocumentView.as_view(), name='document'),
    path('course/', CourseView.as_view(), name='course')
]

