"""
 수업관련 자료 모음 데이타베이스
 
 * DB 구조
  -----------------------------------------------    Many to Many reltaion     -----------------------------------------
         FILE                                   |  <---------------------->    |  TAG                                  |
  -----------------------------------------------                              ----------------------------------------- 
    1. Title                                    |                              |  TOPIC                                |
    2. Curriculum (Algebra, AP, IB..)           |                              -----------------------------------------
    3. Topic (Function, Trig..)                 |                              |  Curriculum                           |
    4. Category (exam, worksheet, lecture note) |                              -----------------------------------------
    5. Difficulty (Hard, Medium, Easy)          |                                      
    6. Note                                     |
    7. file directory                           |
    8. file with key directory                  |
    9. Tag (can be search by tags)              |
    10. publication date                        |
    11. registered dated                        |
 ----------------------------------------------- 



"""
from django.db import models
from django.template.defaultfilters import slugify

COURSES = [
    ("IBHL", "IB HighLevel"),
    ("IBSL", "IB Standard"),
    ("APAB", "AP Calculus AB"),
    ("APBC", "AP Calculus BC"),
    ("PC", "Pre Calculus"),
    ("AL2", "Algebra 2"),
    ("GEO", "Geometry"),
    ("Y9", "Year 9"),
    ("Y10", "Year 10"),
    ("Y11", "Year 11"),
]
def set_file_name(instance, filename):
    
    name, ext = filename.split('.')
    name = f'{instance.title}_{instance.difficulty}'
    fname = '.'.join((name,ext))
    return f'maths/{instance.course}/{instance.category}/{fname}'

class Topic(models.Model):
    """ This class represents the topics related with files """
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"{self.name}"


class File(models.Model):
    """ This class represents the Files """

    CATEGORIES = [
        ('Test', 'Test'),
        ('Worksheet', 'Worksheet'),
        ('Lecture Note', 'Lecture Note')
    ]
    DIFFICULTIES = [
        ('H', 'Hard'),
        ('M', 'Medium'),
        ('E', 'Easy'),
        ('N', 'None')
    ]
    
    title = models.CharField(max_length=255)
    course = models.CharField(max_length=16, choices=COURSES)
    topic = models.ManyToManyField(Topic, related_name='files')
    category = models.CharField(max_length=16, choices=CATEGORIES)
    difficulty = models.CharField(max_length=4, choices=DIFFICULTIES)
    file_location = models.FileField(upload_to=set_file_name)
    key_location = models.FileField(upload_to=set_file_name, null=True, blank=True)
    pub_date = models.DateField(auto_now_add=True)
    note = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f"{self.title}/{self.course}/{self.category}/{self.difficulty}"

    def save(self, *args, **kwargs):
        # 파일 저장 경로 설정
        super(File, self).save(*args, **kwargs)

class Lecture(models.Model):
    """ This class represents the lectures """
    name = models.CharField(max_length=255)
    pub_date = models.DateField(auto_now_add=True)
    course = models.CharField(max_length=16, choices=COURSES)
    lecture_note = models.ManyToManyField(File, related_name='notes', blank=True)
    homework = models.ManyToManyField(File, related_name='homeworks', blank=True)
    test = models.ManyToManyField(File, related_name='tests', blank=True)
    note = models.TextField(max_length=256, blank=True)

    def __str__(self):
        return f"{self.name}"

class PastExamPaper(models.Model):
    """ This class represents the past examination papers"""
    SCHOOLS = [
        ("SASH", "SAS"),
        ("SHID", "SHID")
    ]
    
    name = models.CharField(max_length=255)
    school = models.CharField(max_length=16, choices=SCHOOLS)
    course = models.CharField(max_length=16, choices=COURSES)
    topic = models.ManyToManyField(Topic, related_name='exams')
    paper = models.ManyToManyField(File, related_name='exams')

    def __str__(self):
        return f"{self.name}"

    