from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.db.models import Sum, Count
import json
import traceback
from .models import Activity, Activity_Category, Activity_Tag, Status_Tag, Attentional_Lapse, Lapse_Category, Plan, Todo

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

        # Auto-match with Plan
        # Find overlapping plans on the same date with the same category
        if category:
            overlapping_plans = Plan.objects.filter(
                date=start_time.date(),
                category=category
            )

            # Find the plan with the most overlap
            best_match = None
            max_overlap = 0

            for plan in overlapping_plans:
                # Convert times to minutes for easier calculation
                plan_start_minutes = plan.start_time.hour * 60 + plan.start_time.minute
                plan_end_minutes = plan.end_time.hour * 60 + plan.end_time.minute
                activity_start_minutes = start_time.hour * 60 + start_time.minute
                activity_end_minutes = end_time.hour * 60 + end_time.minute

                # Calculate overlap
                overlap_start = max(plan_start_minutes, activity_start_minutes)
                overlap_end = min(plan_end_minutes, activity_end_minutes)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > max_overlap:
                    max_overlap = overlap
                    best_match = plan

            # Link to plan if there's significant overlap (at least 15 minutes)
            if best_match and max_overlap >= 15:
                activity.planned_from = best_match
                activity.save()

        return JsonResponse({
            'success': True,
            'activity_id': activity.id,
            'duration': activity.duration_in_minutes,
            'lapses_linked': lapses_linked,
            'plan_matched': activity.planned_from_id is not None
        })
    except Exception as e:
        # Print error to terminal for debugging
        print(f"Error in create_activity: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def delete_activity(request):
    """Delete an activity"""
    try:
        data = json.loads(request.body)
        activity_id = data.get('activity_id')

        if not activity_id:
            return JsonResponse({'success': False, 'error': 'Activity ID is required'}, status=400)

        activity = Activity.objects.get(id=activity_id)
        activity.delete()

        return JsonResponse({'success': True})
    except Activity.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Activity not found'}, status=404)
    except Exception as e:
        print(f"Error in delete_activity: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def create_lapse(request):
    """Create new attentional lapse with auto-matching to activity"""
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

        # Auto-match lapse to activity
        # Find activities that overlap with the lapse timestamp
        lapse_time = lapse.timestamp

        overlapping_activities = Activity.objects.filter(
            start_time__lte=lapse_time,
            end_time__gte=lapse_time
        ).order_by('-start_time')  # Most recent first

        if overlapping_activities.exists():
            # Use the most recent overlapping activity
            matched_activity = overlapping_activities.first()
            lapse.activity = matched_activity
            lapse.save(update_fields=['activity'])

            print(f"Auto-matched lapse {lapse.id} to activity {matched_activity.id} ({matched_activity.category.name})")
        else:
            print(f"No matching activity found for lapse at {lapse_time}")

        return JsonResponse({
            'success': True,
            'lapse_id': lapse.id,
            'timestamp': lapse.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'matched_activity_id': lapse.activity.id if lapse.activity else None
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
                'color': activity.category.color if activity.category else '#667eea,#764ba2',
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity_categories'] = Activity_Category.objects.all()
        return context

class PlanView(TemplateView):
    template_name = "echomind/plan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity_categories'] = Activity_Category.objects.all()
        return context

class CalendarView(TemplateView):
    template_name = "echomind/calendar.html"

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
            estimated = float(plan.estimated_hours) if plan.estimated_hours else 0
            actual = actual_hours_by_category.get(category_name, 0)

            plans_data.append({
                'id': plan.id,
                'category': category_name,
                'start_time': plan.start_time.strftime('%H:%M'),
                'end_time': plan.end_time.strftime('%H:%M'),
                'color': plan.category.color,
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

@require_http_methods(["GET"])
def get_plans_by_week(request):
    """Get all plans for a specific week"""
    try:
        # Get week start date (Monday)
        date_str = request.GET.get('date')
        if not date_str:
            date_obj = datetime.now().date()
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Calculate week start (Monday) and end (Sunday)
        week_start = date_obj - timedelta(days=date_obj.weekday())
        week_end = week_start + timedelta(days=6)

        print(f"DEBUG: get_plans_by_week - date_str: {date_str}, week_start: {week_start}, week_end: {week_end}")

        # Get all plans for this week
        plans = Plan.objects.filter(
            date__gte=week_start,
            date__lte=week_end
        ).select_related('category')

        print(f"DEBUG: Found {plans.count()} plans")
        for plan in plans:
            print(f"DEBUG: Plan - date: {plan.date}, category: {plan.category.name}, time: {plan.start_time}-{plan.end_time}")

        # Get all activities for this week
        start_of_week = datetime.combine(week_start, datetime.min.time())
        end_of_week = datetime.combine(week_end, datetime.max.time())

        activities = Activity.objects.filter(
            start_time__gte=start_of_week,
            end_time__lte=end_of_week
        ).select_related('category')

        # Prepare plans data
        plans_data = []
        for plan in plans:
            # Check if there's a matching activity
            has_activity = activities.filter(
                category=plan.category,
                start_time__date=plan.date,
                start_time__time__lte=plan.end_time,
                end_time__time__gte=plan.start_time
            ).exists()

            plans_data.append({
                'id': plan.id,
                'date': plan.date.strftime('%Y-%m-%d'),
                'category': plan.category.name,
                'category_id': plan.category.id,
                'color': plan.category.color,
                'start_time': plan.start_time.strftime('%H:%M'),
                'end_time': plan.end_time.strftime('%H:%M'),
                'note': plan.note or '',
                'has_activity': has_activity
            })

        return JsonResponse({
            'success': True,
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'plans': plans_data
        })
    except Exception as e:
        print(f"Error in get_plans_by_week: {str(e)}")
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
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        estimated_hours = data.get('estimated_hours')
        note = data.get('note', '')

        if not date_str or not category_id or not start_time_str or not end_time_str:
            return JsonResponse({'success': False, 'error': 'Date, category, start_time, and end_time are required'}, status=400)

        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
        category = Activity_Category.objects.get(id=category_id)

        # Calculate estimated_hours if not provided
        if not estimated_hours:
            start_dt = datetime.combine(date_obj, start_time_obj)
            end_dt = datetime.combine(date_obj, end_time_obj)
            delta = end_dt - start_dt
            estimated_hours = round(delta.total_seconds() / 3600, 1)

        plan = Plan.objects.create(
            date=date_obj,
            category=category,
            start_time=start_time_obj,
            end_time=end_time_obj,
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

class StatsView(TemplateView):
    template_name = "echomind/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get period from query params (default: week)
        period = self.request.GET.get('period', 'week')

        # Calculate date range
        now = datetime.now()
        if period == 'today':
            start_date = datetime.combine(now.date(), datetime.min.time())
            end_date = datetime.combine(now.date(), datetime.max.time())
            period_label = "오늘"
        elif period == 'week':
            start_date = datetime.combine(now.date() - timedelta(days=now.weekday()), datetime.min.time())
            end_date = datetime.combine(now.date(), datetime.max.time())
            period_label = "이번주"
        elif period == 'month':
            start_date = datetime.combine(now.replace(day=1).date(), datetime.min.time())
            end_date = datetime.combine(now.date(), datetime.max.time())
            period_label = "이번달"
        else:
            start_date = datetime.combine(now.date() - timedelta(days=7), datetime.min.time())
            end_date = datetime.combine(now.date(), datetime.max.time())
            period_label = "이번주"

        # Get activities in range
        activities = Activity.objects.filter(
            start_time__gte=start_date,
            end_time__lte=end_date
        ).select_related('category')

        # Calculate main metrics
        total_minutes = sum([a.duration_in_minutes or 0 for a in activities])
        net_minutes = sum([a.get_net_duration() for a in activities])

        # Get lapses in range
        lapses = Attentional_Lapse.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        lapse_minutes = sum([l.duration_in_minute or 0 for l in lapses])

        # Calculate focus rate
        focus_rate = round((net_minutes / total_minutes * 100) if total_minutes > 0 else 0, 1)

        # Category analysis
        category_stats = {}
        for activity in activities:
            cat_name = activity.category.name if activity.category else 'Unknown'
            net_duration = activity.get_net_duration()

            if cat_name in category_stats:
                category_stats[cat_name] += net_duration
            else:
                category_stats[cat_name] = net_duration

        # Sort by time (descending)
        category_stats = dict(sorted(category_stats.items(), key=lambda x: x[1], reverse=True))

        # Calculate percentages for categories
        category_data = []
        for cat_name, minutes in category_stats.items():
            hours = round(minutes / 60, 1)
            percentage = round((minutes / net_minutes * 100) if net_minutes > 0 else 0, 1)
            category_data.append({
                'name': cat_name,
                'hours': hours,
                'percentage': percentage
            })

        # Lapse analysis
        lapse_type_counts = lapses.values('lapse_type').annotate(count=Count('id'))
        lapse_stats = []
        total_lapses = lapses.count()
        for item in lapse_type_counts:
            lapse_stats.append({
                'type': dict(Attentional_Lapse.LAPSE_TYPES).get(item['lapse_type'], item['lapse_type']),
                'count': item['count'],
                'percentage': round((item['count'] / total_lapses * 100) if total_lapses > 0 else 0, 1)
            })

        # Plan achievement rate
        plans = Plan.objects.filter(
            date__gte=start_date.date(),
            date__lte=end_date.date()
        ).select_related('category')

        plan_stats = []
        total_planned_hours = 0
        total_actual_hours = 0

        for plan in plans:
            # Get actual activities for this plan's category and date
            plan_activities = Activity.objects.filter(
                category=plan.category,
                start_time__date=plan.date
            )

            actual_minutes = sum([a.get_net_duration() for a in plan_activities])
            actual_hours = actual_minutes / 60
            planned_hours = float(plan.estimated_hours)

            total_planned_hours += planned_hours
            total_actual_hours += actual_hours

            achievement = round((actual_hours / planned_hours * 100) if planned_hours > 0 else 0, 1)

            plan_stats.append({
                'category': plan.category.name,
                'planned': planned_hours,
                'actual': round(actual_hours, 1),
                'achievement': achievement
            })

        overall_achievement = round((total_actual_hours / total_planned_hours * 100) if total_planned_hours > 0 else 0, 1)

        context.update({
            'period': period,
            'period_label': period_label,
            'total_hours': round(total_minutes / 60, 1),
            'net_hours': round(net_minutes / 60, 1),
            'lapse_hours': round(lapse_minutes / 60, 1),
            'focus_rate': focus_rate,
            'category_data': category_data,
            'lapse_count': total_lapses,
            'lapse_avg_duration': round(lapse_minutes / total_lapses) if total_lapses > 0 else 0,
            'lapse_stats': lapse_stats,
            'plan_stats': plan_stats,
            'overall_achievement': overall_achievement,
        })

        return context

# Todo API views
@csrf_exempt
@require_http_methods(["GET"])
def get_todos_by_date(request):
    """Get todos for a specific date"""
    try:
        date_str = request.GET.get('date')
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date parameter required'})

        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        todos = Todo.objects.filter(date=date_obj).select_related('category')

        todo_list = []
        for todo in todos:
            todo_list.append({
                'id': todo.id,
                'date': str(todo.date),
                'category': todo.category.name if todo.category else None,
                'category_id': todo.category.id if todo.category else None,
                'color': todo.category.color if todo.category else None,
                'content': todo.content,
                'is_completed': todo.is_completed,
                'completed_at': todo.completed_at.isoformat() if todo.completed_at else None,
            })

        return JsonResponse({
            'success': True,
            'todos': todo_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def create_todo(request):
    """Create a new todo"""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        category_id = data.get('category_id')
        content = data.get('content')

        if not date_str or not content:
            return JsonResponse({'success': False, 'error': 'Date and content required'})

        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        todo = Todo.objects.create(
            date=date_obj,
            category_id=category_id if category_id else None,
            content=content
        )

        return JsonResponse({
            'success': True,
            'todo': {
                'id': todo.id,
                'date': str(todo.date),
                'category': todo.category.name if todo.category else None,
                'category_id': todo.category.id if todo.category else None,
                'color': todo.category.color if todo.category else None,
                'content': todo.content,
                'is_completed': todo.is_completed,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def toggle_todo(request):
    """Toggle todo completion status"""
    try:
        data = json.loads(request.body)
        todo_id = data.get('todo_id')

        if not todo_id:
            return JsonResponse({'success': False, 'error': 'Todo ID required'})

        todo = Todo.objects.get(id=todo_id)
        todo.is_completed = not todo.is_completed
        todo.completed_at = timezone.now() if todo.is_completed else None
        todo.save()

        return JsonResponse({
            'success': True,
            'is_completed': todo.is_completed
        })
    except Todo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Todo not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def delete_todo(request):
    """Delete a todo"""
    try:
        data = json.loads(request.body)
        todo_id = data.get('todo_id')

        if not todo_id:
            return JsonResponse({'success': False, 'error': 'Todo ID required'})

        todo = Todo.objects.get(id=todo_id)
        todo.delete()

        return JsonResponse({'success': True})
    except Todo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Todo not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})