import json
from datetime import datetime, timedelta, time
from collections import OrderedDict

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, DetailView
from django.db.models import Sum

from .models import Course, Lesson, Student, Tuition, Attendence

#from maths.models import Document, Klass, Lecture, PastExamPaper
# Create your views here.

class Calendar:
    def __init__(self, weekidx):
        """ 오늘 기준으로 이번주 week=0, 지난주는 week=-1, 다음주는 week=1"""
        self._weekidx = int(weekidx) if weekidx else 0
        self._today = datetime.now().date() + timedelta(self._weekidx*7)
        todaynum = self.today.weekday()
        self._thisweek = [self.today + timedelta(i-todaynum) for i in range(7)]
    
    
    # 현재 사용 안함
    def time_sequences(self):
        """ 매 5분단위 시간을 9시~밤12시까지 tuple 형태로 표현된 리스트 반환
            ex) 9시 15분 = (9,15)"""
        start = 10 * 60 
        end = 24 * 60
        times = []
        for i in range(start, end, 5):
            hour = int(i/60)
            minute = i%60
            times.append((hour,minute))
        return times

    def div_property(self, start, end):
        """ html 상에서 수업시간 div의 top과 height property return"""
        top = ((start.hour - 10)*60 + start.minute)*0.8
        height = ((end.hour*60+end.minute) - (start.hour*60+start.minute))*0.8
        duration = start.strftime("%H:%M")+"~"+end.strftime("%H:%M")
        return top, height, duration
        
    @property
    def today(self):
        return self._today
    @property
    def weekidx(self):
        return self._weekidx

    @property
    def thisweek(self):
        return self._thisweek
    
    @property
    def first(self):
        return self.thisweek[0]

    @property
    def last(self):
        return self.thisweek[-1]
    
    @property
    def weekdays(self):
        return ['MON','TUE','WED','THU','FRI','SAT','SUN']

class IndexView(TemplateView):
    def get(self, request, *args, **kwargs):
        context={}
        courses = Course.objects.filter(status=True)
        today = datetime.today().date()
        days=[]
        # 향후 7일동안의 수업일정을 불러옴
        weekdays = ['MON','TUE','WED','THU','FRI','SAT','SUN']
        weekdays_kor = ['월요일','화요일','수요일','목요일','금요일','토요일','일요일']
        for date in [today + + timedelta(i) for i in range(7)]:
            day = weekdays[date.weekday()] #요일
            day_kor = weekdays_kor[date.weekday()] #요일-한글
            work = [date, day_kor] 
            lesson = courses.filter(time__contains=day)
            l = []
            for item in lesson:
                strtime = [t for t in item.time.split(';') if day in t][0] #WED16001730
                start = time(int(strtime[3:5]),int(strtime[5:7]))
                end = time(int(strtime[7:9]),int(strtime[9:]))
                l.append(
                    (item, start, end)
                )
            work.append(l)
            days.append(work)
        context['days'] = days
        context['today'] = today
        return render(request, "tutoring/index.html", context)

class CalendarView(TemplateView):
    #template_name = "tutoring/calendar.html"

    def get(self, request, *args, **kwargs):
        c = Calendar(request.GET.get('week'))
        today = datetime.today().date()
        courses = Course.objects.filter(status=True)
        lessons = Lesson.objects.all()
        dayworks = OrderedDict(MON={},TUE={},WED={},THU={},FRI={},SAT={},SUN={})

        weekdays = ['MON','TUE','WED','THU','FRI','SAT','SUN']
        for idx, date in enumerate(c.thisweek):
            day = weekdays[idx]
            dayworks[day]['done'] = []
            dayworks[day]['todo'] = []

            # 완료된 수업
            lesson = lessons.filter(date=date)
            for item in lesson:
                top, height, duration = c.div_property(item.start, item.end)
                attendees = list(item.attendence_set.all().values_list("student__name", flat=True))
                dayworks[day]['done'].append((item, top, height, duration, attendees))

            # 예정 수업
            # 지금보다 이전날짜는 미래일정에 포함되지 않음
            if date < today:
                continue
            
            course = courses.filter(time__contains=day)
            for item in course:
                strtime = [t for t in item.time.split(';') if day in t][0] #WED16001730
                #한시간 셀의 높이 = 48px
                #top position = ((시간-10)*60 + 분)*(4/5)
                #height = (마친시간-시작시간)(분)*(4/5)
                start = time(int(strtime[3:5]),int(strtime[5:7]))
                end = time(int(strtime[7:9]),int(strtime[9:]))
                top, height, duration = c.div_property(start, end)
                #hour = strtime[3:5] + ':' + strtime[5:7] + '~' + strtime[7:9] + ':' + strtime[9:]  
                dayworks[day]['todo'].append((item, top, height, duration))

        context = {}
        context["dayworks"] = dayworks
        context["thisweek"] = c.thisweek
        context["weekidx"] = c.weekidx
        context["today"] = today
        context["course_pks"] = [c.course.pk for c in lesson] #예정된 수업이 진행되었는지 확인용
        
        return render(request, "tutoring/calendar.html", context)

class CourseView(TemplateView):
    #template_name = "tutoring/course.html"
    def get(self, request, *args, **kwargs):
        courses = Course.objects.all()
        context={}
        context["courses"] = courses
        
        return render(request, "tutoring/course.html", context)

class CourseDetailView(TemplateView):
    #template_name = "tutoring/coursedetail.html"
    def get(self, request, *args, **kwargs):
        lessons = Lesson.objects.filter(course__pk=kwargs['pk'])
        context={}
        context["lessons"] = lessons

        return render(request, "tutoring/course_detail.html", context)

class StudentView(TemplateView):
    #template_name = "tutoring/coursedetail.html"
    def get(self, request, *args, **kwargs):
        students = Student.objects.all()
        context={}
        context["students"] = students
        
        return render(request, "tutoring/student.html", context)

class StudentDetailView(TemplateView):
    #template_name = "tutoring/coursedetail.html"
    def get(self, request, *args, **kwargs):
        student = Student.objects.get(name=kwargs['name'])
        courses = Course.objects.filter(student=student)
        attendences = Attendence.objects.filter(student=student).order_by('-lesson__date')
        tuition = Tuition.objects.filter(student=student)
        #deposit = tuition.aggregate(Sum('deposit'))['deposit__sum']
        #usage = sum([l.lesson.course.tuition for l in attendences])
        context={}
        context["student"] = student
        context["courses"] = courses
        context["attendences"] = attendences[:10] #수업목록 10회만 보임
        context["tuition"] = {
            'records': tuition,
            'deposit': student.total_deposit(),
            'usage': student.balance()
        }
        return render(request, "tutoring/student_detail.html", context)

class StatementView(TemplateView):
    #template_name = "tutoring/coursedetail.html"
    def get(self, request, *args, **kwargs):
        params = dict(request.GET)
        student = Student.objects.get(pk=params.get('student')[0])
        attendences = []
        if params.get('attendences'):
            for at in reversed(params['attendences']):
                attendences.append(Attendence.objects.get(pk=at))
        course = attendences[-1].lesson.course if attendences else None
        context = {}
        context['student'] = student
        context['attendences'] = attendences
        context['course'] = course
        context['tuition'] = Tuition.objects.filter(student=student).order_by('-date').first()
        context['nums'] = len(attendences)
        context['today'] = datetime.today().date()
        return render(request, "tutoring/statement.html", context)