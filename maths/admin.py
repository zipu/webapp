from django.contrib import admin

# Register your models here.
from django.forms.widgets import CheckboxSelectMultiple, TextInput, RadioSelect
from django.db import models
from maths.models import Document, Lecture, PastExamPaper, Topic, Book



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

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    model = Lecture
    filter_horizontal = ('lecture_note','homework','test')

@admin.register(PastExamPaper)
class ExamAdmin(admin.ModelAdmin):
    model = PastExamPaper
    #filter_horizontal = ('course', 'lecture_note','homework','test')

admin.site.register(Topic)
admin.site.register(Book)