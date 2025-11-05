from django.contrib import admin
from .models import Activity_Category, Status_Tag, Activity_Tag, Activity, Attentional_Lapse, Lapse_Category

# Register your models here.

@admin.register(Activity_Category)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Status_Tag)
class StatusTagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Activity_Tag)
class ActivityTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['category', 'start_time', 'end_time', 'duration_in_minutes']
    list_filter = ['category', 'start_time']
    search_fields = ['description']
    filter_horizontal = ['activity_tags', 'status_tags']
    date_hierarchy = 'start_time'

@admin.register(Lapse_Category)
class LapseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Attentional_Lapse)
class AttentionalLapseAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'lapse_type', 'category', 'activity', 'duration_in_minute']
    list_filter = ['lapse_type', 'category', 'timestamp']
    search_fields = ['description']
    date_hierarchy = 'timestamp'
