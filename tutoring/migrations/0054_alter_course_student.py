# Generated by Django 4.1.3 on 2024-05-15 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0053_tuition_note_alter_tuition_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='student',
            field=models.ManyToManyField(blank=True, null=True, to='tutoring.student', verbose_name='학생'),
        ),
    ]
