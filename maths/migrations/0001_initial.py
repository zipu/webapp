# Generated by Django 2.1.4 on 2018-12-24 16:29

from django.db import migrations, models
import maths.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('course', models.CharField(choices=[('IBHL', 'IB HighLevel'), ('IBSL', 'IB Standard'), ('APAB', 'AP Calculus AB'), ('APBC', 'AP Calculus BC'), ('PC', 'Pre Calculus'), ('AL2', 'Algebra 2'), ('GEO', 'Geometry'), ('Y9', 'Year 9'), ('Y10', 'Year 10'), ('Y11', 'Year 11')], max_length=16)),
                ('category', models.CharField(choices=[('Test', 'Test'), ('Worksheet', 'Worksheet'), ('Lecture Note', 'Lecture Note')], max_length=16)),
                ('difficulty', models.CharField(choices=[('H', 'Hard'), ('M', 'Medium'), ('E', 'Easy'), ('N', 'None')], max_length=4)),
                ('file_location', models.FileField(upload_to=maths.models.set_file_name)),
                ('key_location', models.FileField(blank=True, null=True, upload_to=maths.models.set_file_name)),
                ('pub_date', models.DateField(auto_now_add=True)),
                ('note', models.CharField(blank=True, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Lecture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('pub_date', models.DateField(auto_now_add=True)),
                ('course', models.CharField(choices=[('IBHL', 'IB HighLevel'), ('IBSL', 'IB Standard'), ('APAB', 'AP Calculus AB'), ('APBC', 'AP Calculus BC'), ('PC', 'Pre Calculus'), ('AL2', 'Algebra 2'), ('GEO', 'Geometry'), ('Y9', 'Year 9'), ('Y10', 'Year 10'), ('Y11', 'Year 11')], max_length=16)),
                ('note', models.TextField(blank=True, max_length=256)),
                ('homework', models.ManyToManyField(blank=True, related_name='homeworks', to='maths.File')),
                ('lecture_note', models.ManyToManyField(blank=True, related_name='notes', to='maths.File')),
                ('test', models.ManyToManyField(blank=True, related_name='tests', to='maths.File')),
            ],
        ),
        migrations.CreateModel(
            name='PastExamPaper',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('school', models.CharField(choices=[('SASH', 'SAS'), ('SHID', 'SHID')], max_length=16)),
                ('course', models.CharField(choices=[('IBHL', 'IB HighLevel'), ('IBSL', 'IB Standard'), ('APAB', 'AP Calculus AB'), ('APBC', 'AP Calculus BC'), ('PC', 'Pre Calculus'), ('AL2', 'Algebra 2'), ('GEO', 'Geometry'), ('Y9', 'Year 9'), ('Y10', 'Year 10'), ('Y11', 'Year 11')], max_length=16)),
                ('paper', models.ManyToManyField(related_name='exams', to='maths.File')),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='pastexampaper',
            name='topic',
            field=models.ManyToManyField(related_name='exams', to='maths.Topic'),
        ),
        migrations.AddField(
            model_name='file',
            name='topic',
            field=models.ManyToManyField(related_name='files', to='maths.Topic'),
        ),
    ]
