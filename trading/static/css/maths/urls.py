from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import DocumentView, KlassView, KlassDetailView, ExamView, ExamDetailView


urlpatterns = [
    path('', RedirectView.as_view(url='klass', permanent=False)),
    path('document/', DocumentView.as_view(), name='document'),
    path('klass/', KlassView.as_view(), name='klass'),
    path('klass/<int:pk>/', KlassDetailView.as_view(), name='klassdetail'),
    path('exam/', ExamView.as_view(), name='exam'),
    path('exam/<int:pk>/', ExamDetailView.as_view(), name='examdetail'),
]

