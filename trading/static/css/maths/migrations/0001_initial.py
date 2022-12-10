# Generated by Django 2.2.6 on 2019-11-01 15:58

from django.db import migrations, models
import django.db.models.deletion
import maths.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('course', models.CharField(choices=[('IBHL', 'IB HighLevel'), ('IBSL', 'IB Standard'), ('APAB', 'AP Calculus AB'), ('APBC', 'AP Calculus BC'), ('PreCal', 'Pre Calculus'), ('Algebra2', 'Algebra 2'), ('Geometry', 'Geometry'), ('Y9', 'Year 9'), ('Y10', 'Year 10'), ('Y11', 'Year 11'), ('etc', 'etc')], max_length=16)),
                ('category', models.CharField(choices=[('Test', 'Test'), ('Worksheet', 'Worksheet'), ('Note', 'Note'), ('Quiz', 'Quiz'), ('Book', 'Book'), ('Exam', 'Exam')], max_length=16)),
                ('difficulty', models.CharField(choices=[('H', 'Hard'), ('M', 'Medium'), ('E', 'Easy'), ('N', 'None')], max_length=16)),
                ('file', models.FileField(upload_to=maths.models.set_file_name)),
                ('key', models.FileField(blank=True, null=True, upload_to=maths.models.set_key_name)),
                ('reputation', models.IntegerField(default=0)),
                ('pub_date', models.DateField(auto_now_add=True)),
                ('note', models.CharField(blank=True, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Klass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('pub_date', models.DateField()),
                ('course', models.CharField(choices=[('IBHL', 'IB HighLevel'), ('IBSL', 'IB Standard'), ('APAB', 'AP Calculus AB'), ('APBC', 'AP Calculus BC'), ('PreCal', 'Pre Calculus'), ('Algebra2', 'Algebra 2'), ('Geometry', 'Geometry'), ('Y9', 'Year 9'), ('Y10', 'Year 10'), ('Y11', 'Year 11'), ('etc', 'etc')], max_length=16)),
                ('status', models.BooleanField(default=True)),
                ('note', models.TextField(blank=True, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='PastExamPaper',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pub_year', models.DateField()),
                ('exam', models.CharField(choices=[('IB Standard', 'IBSL'), ('IB Highlevel', 'IBHL'), ('AP Calculus AB', 'APAB'), ('AP Calculus BC', 'APBC'), ('AP Statistics', 'AP STAT'), ('A-Level Maths', 'A-Level'), ('SAT Math', 'SAT'), ('SAT2 Math', 'SAT2')], max_length=32)),
                ('paper', models.ManyToManyField(blank=True, to='maths.Document')),
            ],
        ),
        migrations.CreateModel(
            name='Lecture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit', models.IntegerField(default=0)),
                ('name', models.CharField(max_length=255)),
                ('klass', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maths.Klass')),
                ('lecture_note', models.ManyToManyField(blank=True, related_name='lecture_note', to='maths.Document')),
                ('worksheet', models.ManyToManyField(blank=True, related_name='worksheet', to='maths.Document')),
            ],
        ),
        migrations.AddField(
            model_name='document',
            name='topic',
            field=models.ManyToManyField(blank=True, related_name='files', to='maths.Topic'),
        ),
    ]
