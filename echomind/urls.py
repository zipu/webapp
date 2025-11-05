from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import (
    HomeView,
    ActivityLogView,
    LapseLogView,
    ActivityTimelineView,
    get_default_times,
    create_activity,
    create_lapse,
    get_activities_by_date
)

urlpatterns = [
    path('', HomeView.as_view(), name='echomind_home'),
    path('activity-log/', ActivityLogView.as_view(), name='activity_log'),
    path('attentional-lapse/', LapseLogView.as_view(), name='lapse_log'),
    path('timeline/', ActivityTimelineView.as_view(), name='activity_timeline'),
    path('api/default-times/', get_default_times, name='get_default_times'),
    path('api/activity/create/', create_activity, name='create_activity'),
    path('api/lapse/create/', create_lapse, name='create_lapse'),
    path('api/activities/by-date/', get_activities_by_date, name='get_activities_by_date'),
]
