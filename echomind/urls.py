from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView
from .views import (
    HomeView,
    ActivityLogView,
    LapseLogView,
    ActivityTimelineView,
    PlanView,
    StatsView,
    get_default_times,
    create_activity,
    create_lapse,
    get_activities_by_date,
    get_plans_by_date,
    create_plan,
    delete_plan
)

urlpatterns = [
    path('', HomeView.as_view(), name='echomind_home'),
    path('activity-log/', ActivityLogView.as_view(), name='activity_log'),
    path('attentional-lapse/', LapseLogView.as_view(), name='lapse_log'),
    path('timeline/', ActivityTimelineView.as_view(), name='activity_timeline'),
    path('plan/', PlanView.as_view(), name='plan'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('api/default-times/', get_default_times, name='get_default_times'),
    path('api/activity/create/', create_activity, name='create_activity'),
    path('api/lapse/create/', create_lapse, name='create_lapse'),
    path('api/activities/by-date/', get_activities_by_date, name='get_activities_by_date'),
    path('api/plans/by-date/', get_plans_by_date, name='get_plans_by_date'),
    path('api/plan/create/', create_plan, name='create_plan'),
    path('api/plan/delete/', delete_plan, name='delete_plan'),
]
