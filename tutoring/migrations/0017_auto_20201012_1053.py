# Generated by Django 3.0.3 on 2020-10-12 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0016_course_textbook'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendence',
            name='homework',
            field=models.CharField(max_length=250),
        ),
    ]
