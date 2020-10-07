# Generated by Django 3.0.3 on 2020-09-29 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='curriculum',
            name='tution',
        ),
        migrations.AddField(
            model_name='curriculum',
            name='tution_group',
            field=models.IntegerField(default=1, verbose_name='수업료(그룹)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='curriculum',
            name='tution_private',
            field=models.IntegerField(default=1, verbose_name='수업료(개인)'),
            preserve_default=False,
        ),
    ]
