from django.contrib import admin

# Register your models here.
from tutoring.models import Student, Curriculum, Course, Lesson, Tuition, Attendence

admin.site.register(
 [Student, Curriculum, Tuition, Attendence, Lesson]
)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    #model = Course
    filter_horizontal = ('student',)

#@admin.register(Lesson)
#class LessonAdmin(admin.ModelAdmin):
    #model = Course
#    filter_horizontal = ('student',)