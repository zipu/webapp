from django.db import models
from datetime import datetime

def set_file_name(instance, filename):
    """ naming the image file """  
    
    ext = filename.split('.')[-1]
    name = f'{str(int(datetime.now().timestamp()))}'
    fname = '.'.join((name,ext))
    return f'aops/{fname}'

# Create your models here.
class Category(models.Model):
    """ This class represents the categories related with problems """
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"{self.name}"

class Topic(models.Model):
    """ This class represents the topics related with problems """
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"{self.name}"

class Problem(models.Model):
    """ This class represents the Files """
    DIFFICULTIES =[
        (1,1),(2,2),(3,3),(4,4),(5,5)
    ]
    SESSION = [
        ('A', 'A'), ('B','B')
    ]

    question = models.TextField()
    image = models.ImageField(upload_to=set_file_name, blank=True, null=True)
    category = models.ManyToManyField(Category, related_name='problems')
    year = models.PositiveIntegerField()
    session = models.CharField(choices=SESSION, max_length=20)
    topic = models.ManyToManyField(Topic, related_name='problems')
    difficulty = models.PositiveIntegerField(choices=DIFFICULTIES)
    answer = models.CharField(max_length=128, null=True, blank=True)
    note = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f"{self.id}"

    class Meta:
        ordering = ('-id',)