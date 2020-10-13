from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView

from .views import IndexView, CalendarView, CourseView, CourseDetailView, StudentView, StudentDetailView
from .views import StatementView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    #path('',  RedirectView.as_view(url='calendar', permanent=False)),
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('course/', CourseView.as_view(), name='course'),
    path('course/<int:pk>/', CourseDetailView.as_view(), name='coursedetail'),
    path('student/', StudentView.as_view(), name='student'),
    path('student/<str:name>/', StudentDetailView.as_view(), name='studentdetail'),
    path('statement/', StatementView.as_view(), name='statement')
]

