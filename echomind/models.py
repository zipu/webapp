from django.db import models
import random

# Pastel tone color palette for categories
PASTEL_GRADIENTS = [
    '#FFB3BA,#FFDFBA',  # Pink to peach
    '#BAFFC9,#BAE1FF',  # Mint to light blue
    '#FFD9BA,#FFFFBA',  # Peach to light yellow
    '#E0BBE4,#D5AAFF',  # Lavender to light purple
    '#FFDFD3,#FEC8D8',  # Light peach to pink
    '#C7CEEA,#B5EAD7',  # Periwinkle to mint
    '#FFE5B4,#FFDAB9',  # Moccasin gradient
    '#E6E6FA,#D8BFD8',  # Lavender to thistle
    '#B4E7CE,#A7D8DE',  # Mint to powder blue
    '#FFB6C1,#FFA7C4',  # Light pink gradient
    '#D4A5A5,#FFB6C1',  # Rosy brown to pink
    '#AFDBF5,#C9D6FF',  # Sky blue gradient
    '#F5E6E8,#D5C6E0',  # Blush to light purple
    '#B2E2F2,#C7F0DB',  # Light cyan to mint
    '#FFF0DB,#FFE5E5',  # Ivory to light rose
]

# Create your models here.
class Activity_Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=50, default='#667eea,#764ba2', help_text='Gradient colors separated by comma (e.g., #667eea,#764ba2)')

    def save(self, *args, **kwargs):
        # Auto-assign pastel color if still using default
        if self.color == '#667eea,#764ba2':
            # Get all existing colors to avoid duplicates when possible
            existing_colors = set(Activity_Category.objects.exclude(pk=self.pk).values_list('color', flat=True))
            available_colors = [c for c in PASTEL_GRADIENTS if c not in existing_colors]

            # If all colors are used, just pick randomly from palette
            if not available_colors:
                available_colors = PASTEL_GRADIENTS

            self.color = random.choice(available_colors)

        super().save(*args, **kwargs)

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
    planned_from = models.ForeignKey('Plan', on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')

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
        #('narrative drift', 'Narrative Drift'),
        ('intentional lapse', 'Intentional Lapse'),
        #('affective lapse', 'Affective Lapse'),
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
        #('narrative drift', 'Narrative Drift'),
        ('intentional lapse', 'Intentional Lapse'),
        #('affective lapse', 'Affective Lapse'),
    ], default='passive lapse')
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['lapse_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_lapse_type_display()})"

class Plan(models.Model):
    date = models.DateField()
    category = models.ForeignKey(Activity_Category, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, help_text="Estimated time in hours", blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'start_time']

    def __str__(self):
        return f"{self.date} - {self.category.name} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"