from django.contrib import admin


# admin site에서 디폴트로 설정된 사용자 등록 섹션 삭제
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

admin.site.unregister(User)
admin.site.unregister(Group)


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
