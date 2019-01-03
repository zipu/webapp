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
    7. file directory                           |admin/maths/course/
    8. file with key directory                  |
    9. Tag (can be search by tags)              |
    10. publication date                        |
    11. registered dated                        |
 ----------------------------------------------- 



"""
from django.db import models
from django.db.models.signals import post_delete
from datetime import datetime

COURSES = [
    ("IBHL", "IB HighLevel"),
    ("IBSL", "IB Standard"),
    ("APAB", "AP Calculus AB"),
    ("APBC", "AP Calculus BC"),
    ("PreCal", "Pre Calculus"),
    ("Algebra2", "Algebra 2"),
    ("Geometry", "Geometry"),
    ("Y9", "Year 9"),
    ("Y10", "Year 10"),
    ("Y11", "Year 11"),
    ("etc", "etc")
]
def set_file_name(instance, filename):
    
    ext = filename.split('.')[-1]
    name = f'{instance.title}_{instance.category}_'+str(int(datetime.now().timestamp()))
    fname = '.'.join((name,ext))
    return f'maths/{instance.course}/{fname}'

def set_key_name(instance, filename):
    
    ext = filename.split('.')[-1]
    name = f'{instance.title}_{instance.category}_key_'+str(int(datetime.now().timestamp()))
    fname = '.'.join((name,ext))
    return f'maths/{instance.course}/{fname}'


class Topic(models.Model):
    """ This class represents the topics related with files """
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"{self.name}"


class Document(models.Model):
    """ This class represents the Files """

    CATEGORIES = [
        ('Test', 'Test'),
        ('Worksheet', 'Worksheet'),
        ('Note', 'Note'),
        ('Quiz', 'Quiz'),
        ('Book', 'Book')
    ]
    DIFFICULTIES = [
        ('H', 'Hard'),
        ('M', 'Medium'),
        ('E', 'Easy'),
        ('N', 'None')
    ]
    
    title = models.CharField(max_length=255)
    course = models.CharField(max_length=16, choices=COURSES)
    topic = models.ManyToManyField(Topic, related_name='files', blank=True)
    category = models.CharField(max_length=16, choices=CATEGORIES)
    difficulty = models.CharField(max_length=16, choices=DIFFICULTIES)
    file = models.FileField(upload_to=set_file_name)
    key = models.FileField(upload_to=set_key_name, null=True, blank=True)
    reputation = models.IntegerField(default=0)
    pub_date = models.DateField(auto_now_add=True)
    note = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f"{self.title}/{self.course}/{self.category}/{self.difficulty}"


class Lecture(models.Model):
    """ This class represents the lectrues on each course """
    name = models.CharField(max_length=255)
    lecture_note = models.ManyToManyField(Document, related_name='lecture_note', blank=True)
    worksheet = models.ManyToManyField(Document, related_name='worksheet', blank=True)

    def __str__(self):
        return f"{self.name}"


class Klass(models.Model):
    """ This class represents the course description """
    name = models.CharField(max_length=255)
    pub_date = models.DateField()
    course = models.CharField(max_length=16, choices=COURSES)
    lecture = models.ManyToManyField(Lecture) 
    status = models.BooleanField(default=True)
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
    paper = models.ManyToManyField(Document, related_name='exams')

    def __str__(self):
        return f"{self.name}"

# delete model instance associated files
def post_delete_file(sender, instance, *args, **kwargs):
    instance.file.delete(save=False)
    instance.key.delete(save=False)


post_delete.connect(post_delete_file, sender=Document)
