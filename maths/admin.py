from django.contrib import admin

# Register your models here.
from django import forms
from django.forms.widgets import Textarea, CheckboxSelectMultiple, TextInput, RadioSelect
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models
from maths.models import Document, PastExamPaper, Topic, Lecture, Klass


@admin.register(Document)
class FileAdmin(admin.ModelAdmin):
    model = Document
    
    filter_horizontal = ('topic',)
    formfield_overrides ={
        models.CharField: {'widget': TextInput(attrs={'size':'60'})}
    }
    radio_fields = {
        "category": admin.HORIZONTAL,
        "difficulty": admin.HORIZONTAL,
    }

@admin.register(Klass)
class KlassAdmin(admin.ModelAdmin):
    model = Klass
    #inlines = (SortedKlassLectureInline,)
    filter_horizontal = ('lecture',)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':60})},
    }


@admin.register(PastExamPaper)
class ExamAdmin(admin.ModelAdmin):
    model = PastExamPaper
    filter_horizontal = ('paper',)

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    model = Lecture
    filter_horizontal = ('lecture_note','worksheet')

admin.site.register(Topic)