# Generated by Django 4.1.3 on 2024-03-12 20:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0039_rename_notice_last_tution_date_tuitionnotice_notice_last_tuition_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='tuitionnotice',
            name='tuition',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tutoring.tuition'),
        ),
        migrations.AlterField(
            model_name='tuitionnotice',
            name='attendence',
            field=models.ManyToManyField(related_name='notice', to='tutoring.attendence', verbose_name='참여수업`'),
        ),
    ]
