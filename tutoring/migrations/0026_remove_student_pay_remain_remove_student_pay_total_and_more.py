# Generated by Django 4.1.1 on 2022-09-29 03:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0025_student_pay_remain_student_pay_total'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='pay_remain',
        ),
        migrations.RemoveField(
            model_name='student',
            name='pay_total',
        ),
        migrations.AlterField(
            model_name='attendence',
            name='lesson',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='attendence', to='tutoring.lesson'),
        ),
    ]
