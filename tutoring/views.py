import json
from datetime import datetime, timedelta, time
from collections import OrderedDict

from django.middleware import csrf
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views.generic import TemplateView, DetailView
from django.db.models import Sum, Count, F

from .models import Course, Lesson, Student, Tuition, Attendence\
                    ,FinancialItem, Consult, DailyMemo, TuitionNotice\
                    ,Homework, ExtraLessonPlan


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
        """ 매 5분단위 시간을 8시~밤12시까지 tuple 형태로 표현된 리스트 반환
            ex) 9시 15분 = (9,15)"""
        start = 8 * 60 
        end = 24 * 60
        times = []
        for i in range(start, end, 5):
            hour = int(i/60)
            minute = i%60
            times.append((hour,minute))
        return times

    def div_property(self, start, end):
        """ html 상에서 수업시간 div의 top과 height property return"""
        top = ((start.hour - 8)*60 + start.minute)*0.8
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


        weekdays = ['MON','TUE','WED','THU','FRI','SAT','SUN']
        weekdays_kor = ['월요일','화요일','수요일','목요일','금요일','토요일','일요일']
        day = weekdays[today.weekday()] #요일
        courses = courses.filter(time__contains=day)
        extralessons = ExtraLessonPlan.objects.filter(date=today, type='add')
        canceled =  ExtraLessonPlan.objects.filter(date=today, type='remove')
        
        lessons = []
        #추가수업
        for lesson in extralessons:
            lessons.append(
                (lesson.course, lesson.start, lesson.end)
            )

        
        for item in courses:
            if not canceled.filter(course=item):
                strtime = [t for t in item.time.split(';') if day in t][0] #WED16001730
                start = time(int(strtime[3:5]),int(strtime[5:7]))
                end = time(int(strtime[7:9]),int(strtime[9:]))
                lessons.append(
                    (item, start, end)
                )
        
        context['today'] = today
        context['weekday'] = weekdays_kor[today.weekday()]
        context['lessons'] = sorted(lessons, key=lambda x: x[1])

        students_all = Student.objects.filter(status=1)
        students = sorted([(s,s.balance()) for s in students_all if s.balance() < 500], key=lambda x: x[1])
        context['students'] = students

        return render(request, "tutoring/index.html", context)

class CalendarView(TemplateView):
    #template_name = "tutoring/calendar.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get('deletememo'):
            DailyMemo.objects.get(pk=request.GET['deletememo']).delete()
            weekidx = request.GET.get('week')
            response = redirect('calendar')
            response['Location'] += f'?week={weekidx}'
            return response
        
        if request.GET.get('checkmemo'):
            memo = DailyMemo.objects.get(pk=request.GET['checkmemo'])
            memo.checked = not memo.checked
            memo.save()
            
            weekidx = request.GET.get('week')
            response = redirect('calendar')
            response['Location'] += f'?week={weekidx}'
            return response
        
        c = Calendar(request.GET.get('week'))
        today = datetime.today().date()
        courses = Course.objects.filter(status=True)
        lessons = Lesson.objects.all()
        # 오늘의 메모
        memos = DailyMemo.objects.all()
        dayworks = OrderedDict(MON={},TUE={},WED={},THU={},FRI={},SAT={},SUN={})

        weekdays = ['MON','TUE','WED','THU','FRI','SAT','SUN']
        for idx, date in enumerate(c.thisweek):
            day = weekdays[idx]
            dayworks[day]['done'] = []
            dayworks[day]['todo'] = []
            dayworks[day]['date'] = date
            dayworks[day]['memo'] = memos.filter(date=date)
            

            # 완료된 수업
            lesson = lessons.filter(date=date)
            for item in lesson:
                top, height, duration = c.div_property(item.start, item.end)
                attendees = list(item.attendence.all().values_list("student__name", flat=True))
                dayworks[day]['done'].append((item, top, height, duration, attendees))

            # 추가 수업
            extralessons = ExtraLessonPlan.objects.filter(date=date, type='add')
            for extralesson in extralessons:
                start = extralesson.start
                end = extralesson.end
                strtime = start.strftime('%H%M')+end.strftime('%H%M')
                top, height, duration = c.div_property(start, end)
                dayworks[day]['todo'].append((extralesson.course, top, height, duration, strtime))
            
            # 예정 수업
            # 지금보다 이전날짜는 미래일정에 포함되지 않음
            if date < today:
                continue
            
            course = courses.filter(time__contains=day)
            extralessons = ExtraLessonPlan.objects.filter(date=date, type='remove')
            for item in course:
                # 첫 수업 시작일이 오늘보다 이후면 표시하지 않음
                if item.startdate > date:
                    continue
                
                # 삭제된 수업 표시하지 않음
                if extralessons.filter(course=item):
                    continue


                strtime = [t for t in item.time.split(';') if day in t][0] #WED16001730
                #한시간 셀의 높이 = 48px
                #top position = ((시간-10)*60 + 분)*(4/5)
                #height = (마친시간-시작시간)(분)*(4/5)
                start = time(int(strtime[3:5]),int(strtime[5:7]))
                end = time(int(strtime[7:9]),int(strtime[9:]))
                top, height, duration = c.div_property(start, end)
                #hour = strtime[3:5] + ':' + strtime[5:7] + '~' + strtime[7:9] + ':' + strtime[9:]  
                dayworks[day]['todo'].append((item, top, height, duration, strtime[3:]))

        

        context = {}
        context["dayworks"] = dayworks
        context["thisweek"] = c.thisweek
        context["weekidx"] = c.weekidx
        context["today"] = today
        context["course_pks"] = [c.course.pk for c in lesson] #예정된 수업이 진행되었는지 확인용
        
        return render(request, "tutoring/calendar.html", context)

class DailyMemoView(TemplateView):
    def get(self, request, *args, **kwargs):
        context={}
        context['date'] = kwargs['date']
        return render(request, "tutoring/dailymemo.html", context)
    
    def post(self, request, *args, **kwargs):
        params = dict(request.POST)

        DailyMemo.objects.create(
                date=kwargs['date'],
                memo=params['memo'][0],
        )
        return HttpResponse('<script>window.close();window.opener.location.reload();</script>')

class CourseView(TemplateView):
    #template_name = "tutoring/course.html"
    def get(self, request, *args, **kwargs):
        
        courses = Course.objects.filter(status=True)
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

class StatisticsView(TemplateView):
    #template_name = "tutoring/coursedetail.html"
    def get(self, request, *args, **kwargs):
        today = datetime.now()
        if kwargs.get('date'):
            date  = kwargs['date'].split('-')
            year = date[0]
            month = int(date[1])
        else:
            year = today.year
            month = today.month 

        context={}
        students = Student.objects.all()
        context["students_all"] = students
        context["students_enrolled"] = students.filter(status=1)
        context["lessons_stat"] = {}
        context["year"] = year
        context["month"] = month
        
        lessons = Lesson.objects.filter(date__month=month, date__year=year)
        context['lessons_stat']['count'] = [0,0,0,0,0] #[없음,중등,고등,ib/ap,경시]
        context['lessons_stat']['tuition'] = [0,0,0,0,0] #[없음,중등,고등,ib/ap,경시]
        total_tuition = 0
        # 중등:1, 고등:2, IB/AP:3, 경시:4
        for subject in ['math','physics']:
            lessons_by_subject = lessons.filter(course__curriculum__subject=subject)
            context["lessons_stat"][subject] = {}
            context["lessons_stat"][subject]["count"] = [0,0,0,0,0] #[없음,중등,고등,ib/ap,경시]
            context["lessons_stat"][subject]["tuition"] = [0,0,0,0,0] #[없음,중등,고등,ib/ap,경시]
            
            for i in [1,2,3,4]:
                lessons_by_level = lessons_by_subject.filter(course__curriculum__level=i)
                count = lessons_by_level.values('attendence').count()
                tuition = lessons_by_level.annotate(tuition_sum=F('tuition')*Count(F('attendence')))\
                                        .aggregate(sum=Sum('tuition_sum'))['sum'] or 0
                context["lessons_stat"][subject]['count'][i] = count
                context["lessons_stat"][subject]["tuition"][i] = tuition
                context['lessons_stat']['count'][i] += count
                context['lessons_stat']['tuition'][i] += tuition

            context["lessons_stat"][subject]["count_sum"] = sum(context["lessons_stat"][subject]['count'])
            context["lessons_stat"][subject]["tuition_sum"] = sum(context["lessons_stat"][subject]['tuition'])
            total_tuition += context["lessons_stat"][subject]["tuition_sum"]
        
        context["lessons_stat"]["total_count"] = lessons.values('attendence').count()
        context["lessons_stat"]["total_tuition"] = total_tuition
        #print(context["lessons_stat"])


        # 학생통계
        students = students.filter(status=1)
        schools = list(set(students.values_list('school', flat=True)))
        years = [('초6','G6','Y7'), ('중1','G7','Y8'),('중2','G8','Y9'),('중3','G9','Y10'),('고1','G10','Y11'),('고2','G11','Y12'),('고3','G12','Y13')]
        stat = []
        total = [0,0,0,0,0,0,0]
        for school in schools:
            counts = [0,0,0,0,0,0,0]
            students_per_school = students.filter(school=school).values('year2').annotate(count=Count('year2'))
            
            for quanta in students_per_school:
                idx = [ years.index(year) for year in years if quanta['year2'] in year][0]
                counts[idx] = quanta['count']

            stat.append([school,counts,sum(counts)])
            total = [sum(i) for i in zip(total, counts)]
        stat.sort(key=lambda x: x[2], reverse=True)
        
        context['stat'] = stat
        context['total'] = total
        
        return render(request, "tutoring/statistics.html", context)

class StudentDetailView(TemplateView):
    #template_name = "tutoring/coursedetail.html"
    def get(self, request, *args, **kwargs):
        student = Student.objects.get(pk=kwargs['pk'])
        
        # 안내문 삭제
        params = dict(request.GET)
        if 'delete_notice' in params:
            TuitionNotice.objects.get(pk=params['delete_notice'][0]).delete()
            return redirect('studentdetail', pk=student.pk)
        
        courses = Course.objects.filter(student=student, status=True)
        attendences = Attendence.objects.filter(student=student).order_by('-lesson__date')[:20] #최근 20회 수업내역
        tuition = Tuition.objects.filter(student=student).order_by('-date')[:5] #최근 10회 납입내역 
        consult = Consult.objects.filter(student__pk=student.pk) #최근 상담내역
        notices = TuitionNotice.objects.filter(student=student).order_by('-date', '-pk')
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
        context['consult'] = consult
        context['notices'] = notices

        #수업료 납부 팝업 정보
        context['addtuitionhtml'] = render_to_string('tutoring/forms/add_tuition.html',
                                          { 'student': student, 'csrf':csrf.get_token(request)})
        
        return render(request, "tutoring/student_detail.html", context)
    
    def post(self, request, *args, **kwargs):
        subject = request.POST.get('subject')
        print(request.POST)
        # 수업 안내문 pdf파일 업로드 
        if subject == 'noticepdf':
            notice = TuitionNotice.objects.get(pk=request.POST.get('noticepk'))
            notice.pdf = request.FILES['noticepdf']
            notice.save()
            return redirect('studentdetail', pk=notice.student.pk)
        
        # 수업료 납입 기록
        if subject == 'addtuition':
            try:
                Tuition.objects.create(
                    student=Student.objects.get(pk=request.POST.get('student')),
                    date = request.POST.get('date'),
                    deposit = request.POST.get('deposit'),
                    payment = request.POST.get('method')
                ).save()
            except:
                return HttpResponse('내용을 정확히 입력 하세요')
            return HttpResponse('<script>window.close();window.opener.location.reload();</script>')

        

class StatementView(TemplateView):
    #template_name = "tutoring/coursedetail.html"
    def get(self, request, *args, **kwargs):
        params = dict(request.GET)

        # 이미 생성된 안내문 보기
        if 'pk' in kwargs.keys():
            notice = TuitionNotice.objects.get(pk=kwargs.get('pk'))
            history = []
            for course in notice.course.all():
                history.append({
                    'course': course,
                    'attendences': notice.attendence.filter(lesson__course=course)
                })
            
            tuition = {
                'last_payment_date': notice.tuition.date, #최근 납입일
                'lesson_start_date': notice.tuition_start_date,
                'amount': notice.total_tuition,
                'count': notice.num_lessons_for_tuition, #월 수업 횟수
                'fee': notice.tuition_per_lesson, #회당수업료
            }
            
            context = {}
            context['student'] = notice.student
            context['history'] = history #context['attendences'] = attendences
            #context['courses'] = courses
            context['tuition'] = tuition
            context['nums'] = notice.attendence.count()
            #print(context['nums'])
            context['today'] = datetime.today().date()
            context['last_tuition_date'] = True if notice.notice_last_tuition_date else None
            context['guide_next_tuition'] = True if notice.notice_next_tuition  else None
            
            return render(request, "tutoring/forms/statement.html", context)


        # 생성될 안내문 미리ㅣ보기
        else:
            if not params.get('tuition') or len(params.get('tuition')) != 1:
                return HttpResponse("납부 수업료 내역은 한 개만 선택해야 합니다")
            
            if not params.get('attendences'):
                return HttpResponse("진행한 수업을 선택하세요")
            
            if Tuition.objects.get(pk=params.get('tuition')[0]).notice.count() > 0:
                return HttpResponse("선택한 납부내역은 이미 처리되었습니다")
            
            for attendence in params.get('attendences'):
                if Attendence.objects.get(pk=attendence).notice.count() > 0:
                    return HttpResponse("선택된 수업은 이미 수업 안내되었습니다. 확인해보세요.")

            student = Student.objects.get(pk=params.get('student')[0])
            last_tuition = Tuition.objects.get(pk=params.get('tuition')[0])
            courses = Course.objects.filter(pk__in=params.get('course'))
            lessons = Attendence.objects.filter(pk__in=params.get('attendences')) 
            
            #notice = TuitionNotice.objects.get(pk=params.get('notice')[0])
            history = []
            for course in courses.all():
                history.append({
                    'course': course,
                    'lessons': lessons.filter(lesson__course=course)
                })
            
            tuition = {
                'last_payment_date': last_tuition.date, #최근 납입일
                'lesson_start_date': lessons.latest('lesson__date').lesson.date  + timedelta(1), #수업료 적용 날짜
                'fee': courses.first().tuition, #회당수업료
                'amount': 4*courses.first().tuition #다음 납입 수업료 (디폴트: 4회)
            }
            
            context = {}
            context['student'] = student
            context['history'] = history #context['attendences'] = attendences
            context['lessons'] = lessons
            context['courses'] = courses
            context['last_tuition'] = last_tuition
            context['tuition'] = tuition
            context['today'] = datetime.today().date()
            
            return render(request, "tutoring/forms/statement_preview.html", context)
    
    def post(self, request, *args, **kwargs):
        params = dict(request.POST)

        notice = TuitionNotice.objects.create(
            student = Student.objects.get(pk=params.get('student')[0]),
            tuition = Tuition.objects.get(pk=params.get('last_tuition')[0]),
            num_lessons_for_tuition = int(params.get('count')[0]),
            notice_last_tuition_date = True if params.get('last_tuition_date') else False,
            notice_next_tuition = True if params.get('guide_next_tuition') else False

        )
        notice.course.add(*Course.objects.filter(pk__in=params.get('course')))
        notice.attendence.add(*Attendence.objects.filter(pk__in=params.get('lesson')).order_by('-lesson__date'))
        
        notice.tuition_start_date = notice.attendence.latest('lesson__date').lesson.date  + timedelta(1) #수업료 적용 날짜
        notice.total_tuition = params.get('amount')[0]
        notice.tuition_per_lesson = params.get('fee')[0]
        notice.time_per_lesson = params.get('duration')[0]

        history = []
        notice.save()
        return HttpResponse('<script>window.close();window.opener.location.reload();</script>')


        
        

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
            
            # 수업시작시간, 종료시간 
            tm = kwargs['time']
            start = time(int(tm[0:2]), int(tm[2:4]))
            end = time(int(tm[4:6]), int(tm[6:8]))
            context['time'] = [start, end]
            #context['time'] = course.get_time(c.weekdays[date.weekday()])

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
        

        # 예정 수업 목록에서 삭제
        if params['submit'][0] == 'remove':
            ExtraLessonPlan.objects.create(
                course = Course.objects.get(pk=params.get('course')[0]),
                date = params['date'][0],
                type = 'remove'
            ).save()

        #validation
        elif not params['content'][0] or not params['tuition'][0]: 
           return  HttpResponse('수업내용 다시 입력 하세요')
        

        elif params['submit'][0] == 'create':
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
            for file in self.request.FILES.getlist('hwfile'):
                hw = Homework.objects.create(file=file)
                lesson.hwfile.add(hw)

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

            if 'hwfile' in request.POST and not request.POST.get('hwfile'):
                lesson.hwfile.all().delete()
            
            if request.FILES.getlist('hwfile'):
                lesson.hwfile.all().delete()
                for file in request.FILES.getlist('hwfile'):
                    hw = Homework.objects.create()
                    hw.file = file
                    hw.save()
                    lesson.hwfile.add(hw)
            
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
    
class ConsultView(TemplateView):
    def get(self, request, *args, **kwargs):
        context={}
        context['student'] = Student.objects.get(pk=kwargs['pk'])
        context['consult_history'] = Consult.objects.filter(student__pk=kwargs['pk'])
        return render(request, "tutoring/consult.html", context)

class FinancialView(TemplateView):
    #template_name = "tutoring/coursedetail.html"
    def get(self, request, *args, **kwargs):
        today = datetime.now()
        if kwargs.get('date'):
            date  = kwargs['date'].split('-')
            if len(date) == 1:
                year = date[0]
                month = {'year':today.year, 'month':today.month}
            elif len(date) == 2:
                year = date[0]
                month = {'year':date[0], 'month':date[1]}
        else:
            year = today.year
            month = {'year':today.year, 'month':today.month} 

        tuition = Tuition.objects.filter(date__month=month['month'], date__year=month['year'])
        expenditure = FinancialItem.objects.filter(date__year=month['year'], date__month=month['month'], category__level=2)
        income = FinancialItem.objects.filter(date__year=month['year'], date__month=month['month'], category__level=1)

        context={}
        context['year'] = year
        context['month'] = month
        context["summary"]= {
            'tuition': tuition.aggregate(Sum('deposit'))['deposit__sum'],
            'income': income.values('category__name').annotate(amount=Sum('amount')),
            'expenditure': expenditure.values('category__name').annotate(amount=Sum('amount'))
        }
        context["tuition"]=tuition.order_by('-date')
        context["income"]=income.order_by('-date')
        context["expenditure"]=expenditure.order_by('-date')
        context["total_income"]=context['summary']['tuition']+income.aggregate(Sum('amount'))['amount__sum'] if income else context['summary']['tuition'] 
        context["total_expenditure"]= expenditure.aggregate(Sum('amount'))['amount__sum']

        # 해당 년도의 월별 종합
        tuition_by_month = Tuition.objects.filter(date__year=year).values('date__month').annotate(deposit=Sum('deposit'))
        income_by_month = FinancialItem.objects.filter(date__year=year, category__level=1)\
                                        .values('date__month').annotate(amount=Sum('amount'))
        expenditure_by_month = FinancialItem.objects.filter(date__year=year, category__level=2)\
                                        .values('date__month').annotate(amount=Sum('amount'))
        
        lastmonth = int(today.month)+1 if year == today.year else 13
        monthly_total = []
        yearly_total = [0,0,0]
        for i in range(1,lastmonth):
            if tuition_by_month.filter(date__month=i):
                tuition = tuition_by_month.get(date__month=i)['deposit']
            else:
                tuition = 0

            if income_by_month.filter(date__month=i):
                income = income_by_month.get(date__month=i)['amount']
            else:
                income = 0

            if expenditure_by_month.filter(date__month=i):
                expenditure = expenditure_by_month.get(date__month=i)['amount']
            else:
                expenditure = 0
            monthly_total.append([i,tuition+income,expenditure,tuition+income-expenditure])
            yearly_total[0] = yearly_total[0] + tuition + income
            yearly_total[1] = yearly_total[1] + expenditure
            yearly_total[2] = yearly_total[2] + tuition+income-expenditure
        context['monthly_total'] = list(reversed(monthly_total))
        context['yearly_total'] = yearly_total
        
        return render(request, "tutoring/financial.html", context)