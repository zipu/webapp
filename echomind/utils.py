"""
Utility functions for Echo Mind
"""
from .models import Attentional_Lapse, Activity


def rematch_unlinked_lapses():
    """
    Find all lapses that are not linked to any activity and try to match them
    to overlapping activities based on timestamp.

    Returns: dict with statistics
    """
    # Find all lapses without activity
    unlinked_lapses = Attentional_Lapse.objects.filter(activity__isnull=True)

    total = unlinked_lapses.count()
    matched = 0
    not_matched = 0

    print(f"Found {total} unlinked lapses")

    for lapse in unlinked_lapses:
        lapse_time = lapse.timestamp

        # Find activities that overlap with the lapse timestamp
        overlapping_activities = Activity.objects.filter(
            start_time__lte=lapse_time,
            end_time__gte=lapse_time
        ).order_by('-start_time')  # Most recent first

        if overlapping_activities.exists():
            matched_activity = overlapping_activities.first()
            lapse.activity = matched_activity
            lapse.save(update_fields=['activity'])

            matched += 1
            print(f"✓ Matched lapse {lapse.id} ({lapse.timestamp}) to activity {matched_activity.id} ({matched_activity.category.name})")
        else:
            not_matched += 1
            print(f"✗ No match found for lapse {lapse.id} at {lapse.timestamp}")

    result = {
        'total': total,
        'matched': matched,
        'not_matched': not_matched
    }

    print("\n" + "="*50)
    print(f"Summary:")
    print(f"  Total unlinked lapses: {total}")
    print(f"  Successfully matched: {matched}")
    print(f"  No match found: {not_matched}")
    print("="*50)

    return result
