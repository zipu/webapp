from django.db import models

# Create your models here.
class Activity_Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Status_Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Activity_Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Activity_Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tags')

    def __str__(self):
        return self.name

class Activity(models.Model):
    category = models.ForeignKey(Activity_Category, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    duration_in_minutes = models.IntegerField(blank=True, null=True)
    activity_tags = models.ManyToManyField(Activity_Tag, blank=True, related_name='activities')
    status_tags = models.ManyToManyField(Status_Tag, blank=True, related_name='activities')

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_in_minutes = round(delta.total_seconds() / 60, 1)
        super().save(*args, **kwargs)

    def get_net_duration(self):
        """Get actual activity duration excluding lapses"""
        if not self.duration_in_minutes:
            return 0

        # Sum up all lapse durations for this activity
        from django.db.models import Sum
        lapse_total = self.attentional_lapse_set.filter(
            duration_in_minute__isnull=False
        ).aggregate(
            total=Sum('duration_in_minute')
        )['total'] or 0

        # Return net duration (total - lapses)
        net = self.duration_in_minutes - lapse_total
        return max(net, 0)  # Ensure non-negative

    def __str__(self):
        return f"{self.category.name if self.category else 'Unknown'} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        ordering = ['-start_time']

class Attentional_Lapse(models.Model):
    LAPSE_TYPES = [
        ('passive lapse', 'Passive Lapse'),
        ('narrative drift', 'Narrative Drift'),
        ('intentional lapse', 'Intentional Lapse'),
        ('affective lapse', 'Affective Lapse'),
    ]
    lapse_type = models.CharField(max_length=20, choices=LAPSE_TYPES, default='passive lapse')
    timestamp = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey('Lapse_Category', on_delete=models.SET_NULL, null=True)
    activity = models.ForeignKey(Activity, blank=True, null=True, on_delete=models.SET_NULL)
    duration_in_minute = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        category_name = self.category.name if self.category else 'Unknown'
        return f"{self.get_lapse_type_display()} - {category_name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Lapse_Category(models.Model):
    name = models.CharField(max_length=100)
    lapse_type = models.CharField(max_length=20, choices=[
        ('passive lapse', 'Passive Lapse'),
        ('narrative drift', 'Narrative Drift'),
        ('intentional lapse', 'Intentional Lapse'),
        ('affective lapse', 'Affective Lapse'),
    ], default='passive lapse')
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['lapse_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_lapse_type_display()})"

class Plan(models.Model):
    date = models.DateField()
    category = models.ForeignKey(Activity_Category, on_delete=models.CASCADE)
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, help_text="Estimated time in hours")
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'category']

    def __str__(self):
        return f"{self.date} - {self.category.name} ({self.estimated_hours}h)"