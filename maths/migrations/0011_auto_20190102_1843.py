# Generated by Django 2.1.4 on 2019-01-02 18:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maths', '0010_auto_20190102_1832'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='klass',
            name='lecture',
        ),
        migrations.RemoveField(
            model_name='lecture',
            name='lecture_note',
        ),
        migrations.RemoveField(
            model_name='lecture',
            name='worksheet',
        ),
        migrations.DeleteModel(
            name='Klass',
        ),
        migrations.DeleteModel(
            name='Lecture',
        ),
    ]