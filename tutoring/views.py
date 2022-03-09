import json
from datetime import datetime, timedelta, time
from collections import OrderedDict

from django.http import HttpResponse
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
        courses = Course.objects.filter(status=True).all()
        #courses = Course.objects.filter(status=True)
        today = datetime.today().date()

        days=[]
        # 향후 7일동안의 수업일정을 불러옴
        weekdays = ['MON','TUE','WED','THU','FRI','SAT','SUN']
        weekdays_kor = ['월요일','화요일','수요일','목요일','금요일','토요일','일요일']
        for date in [today + timedelta(i) for i in range(7)]:
            day = weekdays[date.weekday()] #요일
            day_kor = weekdays_kor[date.weekday()] #요일-한글
            work = [date, day_kor] 
            #lesson = [l for l in courses if day in l]
            lesson = courses.filter(time__contains=day)
            l = []
            for item in lesson:
                strtime = [t for t in item.time.split(';') if day in t][0] #WED16001730
                start = time(int(strtime[3:5]),int(strtime[5:7]))
                end = time(int(strtime[7:9]),int(strtime[9:]))
                l.append(
                    (item, start, end)
                )
            #print(l)
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
            dayworks[day]['date'] = date

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
        attendences = Attendence.objects.filter(student=student).order_by('-lesson__date')[:20] #최근 20회 수업내역
        tuition = Tuition.objects.filter(student=student).order_by('-date')[:10] #최근 10회 납입내역 
        #deposit = tuition.aggregate(Sum('deposit'))['deposit__sum']
        #usage = sum([l.lesson.course.tuition for l in attendences])
        context={}
        context["student"] = student
        context["courses"] = courses
        context["attendences"] = attendences
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
        #print(params)
        student = Student.objects.get(pk=params.get('student')[0])
        attendences = []
        if params.get('attendences'):
            for at in reversed(params['attendences']):
                attendences.append(Attendence.objects.get(pk=at))
        #course = attendences[-1].lesson.course if attendences else None
        if params.get('course'):
            course = Course.objects.get(pk=params['course'][0])
        else:
            course = None

        tuition = {
            'last_payment_date': Tuition.objects.filter(student=student).order_by('-date').first().date, #최근 납입일
            'lesson_start_date': attendences[-1].lesson.date + timedelta(1) if attendences else None, #수업료 적용 날짜
            'amount': course.tuition * 4 if course else None, #총납부액
            'fee': course.tuition if course else None, #회당수업료
        }
        
        context = {}
        context['student'] = student
        context['attendences'] = attendences
        context['course'] = course
        context['tuition'] = tuition
        context['nums'] = len(attendences)
        context['today'] = datetime.today().date()
        context['last_tuition_date'] = True if params.get('last_tuition_date') else None
        context['guide_next_tuition'] = True if params.get('guide_next_tuition') else None
        return render(request, "tutoring/statement.html", context)

class PostLessonView(TemplateView):
    def get(self, request, *args, **kwargs):
        # 수업입력
        if 'course' in kwargs.keys():
            c = Calendar(0)
            course = Course.objects.get(pk=kwargs['course'])
            date = datetime.strptime(kwargs['date'], '%Y-%m-%d')
            context={}
            context['course'] = course
            context['date'] = date
            context['time'] = course.get_time(c.weekdays[date.weekday()])

            return render(request, "tutoring/post_lesson.html", context)

        #입력된 수업 확인
        elif 'lesson' in kwargs.keys():
            lesson = Lesson.objects.get(pk=kwargs['lesson'])
            context={}
            context['lesson'] = lesson 
            context['course'] = lesson.course
            context['date'] = lesson.date
            context['time'] = (lesson.start, lesson.end)
            context['attendence'] = Attendence.objects.filter(lesson=lesson)
            context['students'] = [i.student.pk for i in context['attendence']]

            return render(request, "tutoring/post_lesson.html", context)


    def post(self, request, *args, **kwargs):
        params = dict(request.POST)
        #validation
        if not params['content'][0] or not params['tuition'][0]: 
           return  HttpResponse('수업내용 다시 입력 하세요')

        if params['submit'][0] == 'create':
            course = Course.objects.get(pk=params.get('course')[0])
            lesson = Lesson.objects.create(
                course=course,
                tuition=params['tuition'][0],
                date=params['date'][0],
                start=params['start'][0],
                end=params['end'][0],
                name=params['content'][0],
                topic=params['topic'][0],
                homework=params['homework'][0],
                note=params['note'][0]
            )

            for pk in params['students']:
                if params[f'attendence_{pk}'][0] == '1':
                    student = Student.objects.get(pk=pk)
                    Attendence.objects.create(
                        lesson=lesson,
                        student=student,
                        homework=params[f'homework_{pk}'][0],
                        note=params[f'student-note_{pk}'][0],
                    ).save()

            lesson.save()

        elif params['submit'][0] == 'update':
            lesson = Lesson.objects.get(pk=params.get('lesson')[0])
            lesson.tuition = params['tuition'][0]
            lesson.date=params['date'][0]
            lesson.start=params['start'][0]
            lesson.end=params['end'][0]
            lesson.name=params['content'][0]
            lesson.topic=params['topic'][0]
            lesson.homework=params['homework'][0]
            lesson.note=params['note'][0]

            for pk in params['students']:
                atts = Attendence.objects.filter(lesson=lesson).filter(student=pk)
                if atts:
                    if params[f'attendence_{pk}'][0] == '1':
                        att = atts[0]
                        att.homework = params[f'homework_{pk}'][0]
                        att.note = params[f'student-note_{pk}'][0]
                        att.save()
                    elif params[f'attendence_{pk}'][0] == '0':
                        atts[0].delete()
                else:
                    if params[f'attendence_{pk}'][0] == '1':
                        student = Student.objects.get(pk=pk)
                        Attendence.objects.create(
                            lesson=lesson,
                            student=student,
                            homework=params[f'homework_{pk}'][0],
                            note=params[f'student-note_{pk}'][0],
                        ).save()
            lesson.save()

        elif params['submit'][0] == 'delete':
            lesson = Lesson.objects.get(pk=params.get('lesson')[0])
            atts = Attendence.objects.filter(lesson=lesson)
            for att in atts:
                att.delete()
            lesson.delete()

        return HttpResponse('<script>window.close();window.opener.location.reload();</script>')