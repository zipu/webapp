# Generated by Django 2.1.4 on 2018-12-31 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maths', '0002_auto_20181230_1752'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='homework',
        ),
        migrations.RemoveField(
            model_name='course',
            name='lecture_note',
        ),
        migrations.RemoveField(
            model_name='course',
            name='test',
        ),
        migrations.AlterField(
            model_name='course',
            name='pub_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='document',
            name='difficulty',
            field=models.CharField(choices=[('Hard', 'Hard'), ('Medium', 'Medium'), ('Easy', 'Easy'), ('None', 'None')], max_length=4),
        ),
    ]