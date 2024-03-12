# Generated by Django 4.1.3 on 2024-03-12 10:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0035_curriculum_subject'),
    ]

    operations = [
        migrations.CreateModel(
            name='TuitionNotice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now=True)),
                ('last_payment_date', models.DateField(blank=True, null=True)),
                ('num_lessons', models.SmallIntegerField(blank=True, null=True)),
                ('textbook', models.CharField(blank=True, max_length=100, null=True)),
                ('tuition_per_lesson', models.IntegerField(blank=True, null=True)),
                ('time_per_lesson', models.IntegerField(blank=True, null=True)),
                ('num_lessons_for_tuition', models.SmallIntegerField(blank=True, null=True)),
                ('total_tuition', models.IntegerField(blank=True, null=True)),
                ('tuition_start_date', models.DateField(blank=True, null=True)),
                ('attendence', models.ManyToManyField(to='tutoring.attendence', verbose_name='참여수업`')),
                ('curriculum', models.ManyToManyField(to='tutoring.curriculum', verbose_name='과정')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tutoring.student')),
            ],
        ),
    ]
