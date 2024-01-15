from django.db import models
from django.db.models import Sum

from datetime import datetime, time

SCHOOLS = [
    ('SASPX','SASPX'),
    ('SASPD','SASPD'), 
    ('BISSPD','BISSPD'),
    ('BISSPX','BISSPX'),
    ('SHID','SHID'),
    ('SCIS','SCIS'),
    ('YCIS','YCIS'),
    ('SSIS','SSIS'),
    ('한국학교', '한국학교'),
]


class Student(models.Model):
    """ This class represents the categories related with problems """
    # 개인정보
    name = models.CharField(max_length=64) #이름
    date = models.DateField(verbose_name="등록일")
    wechat_id = models.CharField(max_length=64) #부모님 위챗
    school = models.CharField(max_length=64, choices=SCHOOLS) #학교
    year = models.PositiveIntegerField() #학년
    status = models.BooleanField() #수강상태
    region = models.CharField(max_length=64) #거주지역
    address = models.CharField(max_length=250, blank=True, null=True)
    note = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    # 납입 잔액
    def balance(self):
        total = self.total_deposit()

        usage = Lesson.objects.filter(attendence__student=self).\
                aggregate(Sum('tuition'))['tuition__sum']
        #    ['lesson__tuition__sum']
        #usage = Attendence.objects.filter(student=self).aggregate(Sum('lesson__tuition'))\
        #    ['lesson__tuition__sum']
        #attendences = Attendence.objects.filter(student=self)
        #usage = sum([l.lesson.tuition for l in attendences] )
        balance = total - usage if usage else total
        return balance
    
    def total_deposit(self):
        return Tuition.objects.filter(student=self)\
                .aggregate(Sum('deposit'))['deposit__sum'] or 0

    class Meta:
        ordering = ('-status','-date')

class Curriculum(models.Model):
    """ 교육과정 """
    name = models.CharField(max_length=64, unique=True)
    #tution_private = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="수업료(개인)")
    #tution_group = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="수업료(그룹)")
    topics = models.TextField(blank=True, null=True) #단원명 (세미콜론;으로 구분하여 입력하고 parsing하여 사용)
    def __str__(self):
        return f"{self.name}"

class Course(models.Model):
    """ 수업 """
    name = models.CharField(max_length=64) #수업명
    curriculum = models.ForeignKey(Curriculum, on_delete=models.PROTECT) #과정
    startdate = models.DateField() #수업개설일
    duration = models.IntegerField(verbose_name="진행시간(분)", default=90) #수업진행시간
    # 수업시간
    # 수요일 3시-4시30분 일요일 4시-5시30분의 경우
    # WED15001630;SUN16001730 으로 저장 후 parsing하여 사용
    time = models.CharField(
        verbose_name="수업시간",
        max_length=250,
        help_text="수요일 3시-4시30분 일요일 4시-5시30분의 경우\
                   WED15001630;SUN16001730"
    )
    student = models.ManyToManyField("Student", verbose_name="학생")
    textbook = models.CharField(max_length=50, blank=True, null=True, verbose_name="주교재")
    tuition = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="수업료")
    status = models.BooleanField(verbose_name="진행상태")

    def __str__(self):
        return f"{self.name}"
    
    def get_time(self, weekday):
        """ 요일을 입력하면 그날의 수업시간 반환 """
        strtime = [i for i in self.time.split(';') if weekday in i]
        if not strtime:
            return None
        else:
            tm = strtime[0][3:]
            start = time(int(tm[0:2]), int(tm[2:4]))
            end = time(int(tm[4:6]), int(tm[6:8]))
            return start, end
        

    
    class Meta:
        ordering = ('-status','-startdate',)

class Lesson(models.Model):
    """ 상세 수업 내용 """
    course = models.ForeignKey("Course", on_delete=models.PROTECT) #수업
    tuition = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="수업료")
    date = models.DateField(verbose_name="날짜")
    start = models.TimeField(verbose_name="시작시간")
    end = models.TimeField(verbose_name="마친시간")
    name = models.CharField(max_length=64, verbose_name="수업내용")
    #student = models.ManyToManyField("Student", verbose_name="출석학생")
    topic = models.CharField(max_length=256, verbose_name="단원", blank=True, null=True)
    homework = models.CharField(max_length=256, verbose_name="숙제", blank=True, null=True)
    note = models.CharField(max_length=128, blank=True, null=True) #비고

    def __str__(self):
        return f"[{self.date}]({self.course.name}) {self.name} "

    class Meta:
        ordering = ('-date', '-start')
    
class Attendence(models.Model):
    """ 출결상황 """
    HOMEWORK = [
        ('1', "잘해옴"),
        ('2', "부족"),
        ('3', "안함"),
        ('4', "")
    ]
    lesson = models.ForeignKey("Lesson", on_delete=models.PROTECT, related_name="attendence")
    student = models.ForeignKey("Student", on_delete=models.PROTECT)
    homework = models.CharField(choices=HOMEWORK, blank=True, null=True, max_length=250)
    note = models.CharField(max_length=250, blank=True, null=True)
    #checked = models.BooleanField(default=False) #안내문 작성된 수업 

    def __str__(self):
        return f"[{self.lesson.name}]{self.student.name} "
    
    def save(self, *args, **kwargs):
        if self.lesson.course.student.filter(pk=self.student.pk).exists():
            super(Attendence, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('lesson', 'student',)

class Tuition(models.Model):
    """ 수업료 납부 내역 """
    METHOD = [
        ("위챗페이", "위챗페이"),
        ("즈푸바오", "즈푸바오"),
        ("현금", "현금")
    ]

    student = models.ForeignKey("Student", on_delete=models.CASCADE) #학생
    date = models.DateField() #날짜
    deposit = models.DecimalField(max_digits=8, decimal_places=2) #납입액
    payment = models.CharField(max_length=250, choices=METHOD) #비고
    def __str__(self):
        return f"[{self.date}]({self.student.name}) {self.deposit} "


class FinancialCategory(models.Model):
    """ 수입/지출 항목 종류 """
    LEVEL = [(2,"지출"), (1,"수입")]
    
    level = models.PositiveSmallIntegerField(choices=LEVEL) #수입/지출 선택
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"[{self.level}]{self.name}"
    
class FinancialItem(models.Model):
    """ 수입/지출 항목 """
    date = models.DateField()
    category = models.ForeignKey("FinancialCategory", on_delete=models.PROTECT) #항목
    amount = models.DecimalField(max_digits=8, decimal_places=2) #금액
    note = models.CharField(max_length=100, blank=True, null=True) #비고

    def __str__(self):
        return f"[{self.category}]{self.amount}"



class Consult(models.Model):
    """ 상담 내역 기록 """
    student = models.ForeignKey("Student", on_delete=models.PROTECT) #항목
    date = models.DateField()
    tag = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField()

    def __str__(self):
        return f"[{self.student.name}]{self.date}"

class DailyMemo(models.Model):
    """ 일별 메모사항 """
    date = models.DateField()
    memo = models.TextField()
    checked = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.pk}]{self.date}"
