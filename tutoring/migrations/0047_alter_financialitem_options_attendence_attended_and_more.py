# Generated by Django 4.1.3 on 2024-04-10 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0046_extralessonplan_type_alter_extralessonplan_end_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='financialitem',
            options={'ordering': ('-date',)},
        ),
        migrations.AddField(
            model_name='attendence',
            name='attended',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='status',
            field=models.SmallIntegerField(choices=[(1, '등록'), (2, '퇴원'), (3, '졸업'), (4, '미등록'), (5, '대기')]),
        ),
    ]
