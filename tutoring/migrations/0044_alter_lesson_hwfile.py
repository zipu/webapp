# Generated by Django 4.1.3 on 2024-03-17 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0043_homework_lesson_hwfile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='hwfile',
            field=models.ManyToManyField(to='tutoring.homework', verbose_name='숙제파일'),
        ),
    ]
