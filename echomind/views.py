from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
import traceback
from .models import Activity, Activity_Category, Activity_Tag, Status_Tag, Attentional_Lapse, Lapse_Category

class HomeView(TemplateView):
    template_name = "echomind/home.html"

class ActivityLogView(TemplateView):
    template_name = "echomind/activity_log.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Activity_Category.objects.all()
        context['activity_tags'] = Activity_Tag.objects.all()
        context['status_tags'] = Status_Tag.objects.all()
        return context

class LapseLogView(TemplateView):
    template_name = "echomind/lapse_log.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lapse_categories'] = Lapse_Category.objects.all()
        return context

@require_http_methods(["GET"])
def get_default_times(request):
    """Get default start/end times for new activity"""
    latest_activity = Activity.objects.order_by('-end_time').first()

    # Use naive datetime (USE_TZ = False)
    now = datetime.now()
    start_time = latest_activity.end_time if latest_activity else now
    end_time = now

    return JsonResponse({
        'start_time': start_time.strftime('%Y-%m-%dT%H:%M'),
        'end_time': end_time.strftime('%Y-%m-%dT%H:%M')
    })

@csrf_exempt
@require_http_methods(["POST"])
def create_activity(request):
    """Create new activity and auto-link lapses"""
    try:
        data = json.loads(request.body)

        category_id = data.get('category_id')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        description = data.get('description', '')
        activity_tag_ids = data.get('activity_tags', [])
        status_tag_ids = data.get('status_tags', [])

        # Convert string to naive datetime (USE_TZ = False)
        start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

        category = Activity_Category.objects.get(id=category_id) if category_id else None

        activity = Activity.objects.create(
            category=category,
            start_time=start_time,
            end_time=end_time,
            description=description
        )

        if activity_tag_ids:
            activity.activity_tags.set(activity_tag_ids)

        if status_tag_ids:
            activity.status_tags.set(status_tag_ids)

        # Auto-link lapses that occurred during this activity
        lapses_linked = Attentional_Lapse.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time,
            activity__isnull=True
        ).update(activity=activity)

        return JsonResponse({
            'success': True,
            'activity_id': activity.id,
            'duration': activity.duration_in_minutes,
            'lapses_linked': lapses_linked
        })
    except Exception as e:
        # Print error to terminal for debugging
        print(f"Error in create_activity: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def create_lapse(request):
    """Create new attentional lapse"""
    try:
        data = json.loads(request.body)

        lapse_type = data.get('lapse_type')
        category_id = data.get('category_id')
        duration = data.get('duration_in_minute')
        description = data.get('description', '')

        if not lapse_type:
            return JsonResponse({'success': False, 'error': 'Lapse type is required'}, status=400)

        category = Lapse_Category.objects.get(id=category_id) if category_id else None

        lapse = Attentional_Lapse.objects.create(
            lapse_type=lapse_type,
            category=category,
            duration_in_minute=duration,
            description=description
        )

        return JsonResponse({
            'success': True,
            'lapse_id': lapse.id,
            'timestamp': lapse.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        # Print error to terminal for debugging
        print(f"Error in create_lapse: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)