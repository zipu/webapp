from django.contrib import admin

# Register your models here.
from aops.models import Problem, Topic, Category

admin.site.register(
 [Problem, Category, Topic]
)