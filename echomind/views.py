from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
import traceback
from .models import Activity, Activity_Category, Activity_Tag, Status_Tag, Attentional_Lapse, Lapse_Category, Plan

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

@require_http_methods(["GET"])
def get_activities_by_date(request):
    """Get all activities for a specific date"""
    try:
        date_str = request.GET.get('date')
        if not date_str:
            # Default to today
            date_obj = datetime.now().date()
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get all activities that overlap with this date
        start_of_day = datetime.combine(date_obj, datetime.min.time())
        end_of_day = datetime.combine(date_obj, datetime.max.time())

        activities = Activity.objects.filter(
            start_time__lte=end_of_day,
            end_time__gte=start_of_day
        ).select_related('category').prefetch_related('activity_tags', 'status_tags')

        activities_data = []
        for activity in activities:
            # Get lapses associated with this activity
            lapses = Attentional_Lapse.objects.filter(activity=activity).select_related('category')
            lapses_data = [{
                'id': lapse.id,
                'type': lapse.get_lapse_type_display(),
                'category': lapse.category.name if lapse.category else 'Unknown',
                'timestamp': lapse.timestamp.strftime('%H:%M'),
                'duration': lapse.duration_in_minute,
                'description': lapse.description or ''
            } for lapse in lapses]

            activities_data.append({
                'id': activity.id,
                'category': activity.category.name if activity.category else 'Unknown',
                'start_time': activity.start_time.strftime('%Y-%m-%d %H:%M'),
                'end_time': activity.end_time.strftime('%Y-%m-%d %H:%M'),
                'description': activity.description or '',
                'duration': activity.duration_in_minutes,
                'net_duration': activity.get_net_duration(),
                'activity_tags': [tag.name for tag in activity.activity_tags.all()],
                'status_tags': [tag.name for tag in activity.status_tags.all()],
                'lapses': lapses_data
            })

        return JsonResponse({
            'success': True,
            'date': date_obj.strftime('%Y-%m-%d'),
            'activities': activities_data
        })
    except Exception as e:
        print(f"Error in get_activities_by_date: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

class ActivityTimelineView(TemplateView):
    template_name = "echomind/activity_timeline.html"

class PlanView(TemplateView):
    template_name = "echomind/plan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity_categories'] = Activity_Category.objects.all()
        return context

@require_http_methods(["GET"])
def get_plans_by_date(request):
    """Get all plans for a specific date with actual activity comparison"""
    try:
        date_str = request.GET.get('date')
        if not date_str:
            date_obj = datetime.now().date()
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Get plans for this date
        plans = Plan.objects.filter(date=date_obj).select_related('category')

        # Get actual activities for this date
        start_of_day = datetime.combine(date_obj, datetime.min.time())
        end_of_day = datetime.combine(date_obj, datetime.max.time())

        activities = Activity.objects.filter(
            start_time__lte=end_of_day,
            end_time__gte=start_of_day
        ).select_related('category')

        # Calculate actual hours by category
        actual_hours_by_category = {}
        for activity in activities:
            category_name = activity.category.name if activity.category else 'Unknown'
            net_duration_minutes = activity.get_net_duration()
            net_duration_hours = net_duration_minutes / 60

            if category_name in actual_hours_by_category:
                actual_hours_by_category[category_name] += net_duration_hours
            else:
                actual_hours_by_category[category_name] = net_duration_hours

        # Prepare plans data with comparison
        plans_data = []
        for plan in plans:
            category_name = plan.category.name
            estimated = float(plan.estimated_hours)
            actual = actual_hours_by_category.get(category_name, 0)

            plans_data.append({
                'id': plan.id,
                'category': category_name,
                'estimated_hours': estimated,
                'actual_hours': round(actual, 1),
                'difference': round(actual - estimated, 1),
                'note': plan.note or ''
            })

        return JsonResponse({
            'success': True,
            'date': date_obj.strftime('%Y-%m-%d'),
            'plans': plans_data
        })
    except Exception as e:
        print(f"Error in get_plans_by_date: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def create_plan(request):
    """Create new plan"""
    try:
        data = json.loads(request.body)

        date_str = data.get('date')
        category_id = data.get('category_id')
        estimated_hours = data.get('estimated_hours')
        note = data.get('note', '')

        if not date_str or not category_id or not estimated_hours:
            return JsonResponse({'success': False, 'error': 'Date, category, and estimated hours are required'}, status=400)

        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        category = Activity_Category.objects.get(id=category_id)

        plan = Plan.objects.create(
            date=date_obj,
            category=category,
            estimated_hours=estimated_hours,
            note=note
        )

        return JsonResponse({
            'success': True,
            'plan_id': plan.id
        })
    except Exception as e:
        print(f"Error in create_plan: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def delete_plan(request):
    """Delete a plan"""
    try:
        data = json.loads(request.body)
        plan_id = data.get('plan_id')

        if not plan_id:
            return JsonResponse({'success': False, 'error': 'Plan ID is required'}, status=400)

        plan = Plan.objects.get(id=plan_id)
        plan.delete()

        return JsonResponse({'success': True})
    except Plan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plan not found'}, status=404)
    except Exception as e:
        print(f"Error in delete_plan: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)