# Generated by Django 4.1.3 on 2024-03-03 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0034_alter_student_options_curriculum_level_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='curriculum',
            name='subject',
            field=models.CharField(choices=[('math', '수학'), ('physics', '물리')], default='math', max_length=100),
            preserve_default=False,
        ),
    ]
