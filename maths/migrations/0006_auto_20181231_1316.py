# Generated by Django 2.1.4 on 2018-12-31 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maths', '0005_auto_20181231_1305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='difficulty',
            field=models.CharField(choices=[('Hard', 'Hard'), ('Medium', 'Medium'), ('Easy', 'Easy'), ('None', 'None')], max_length=16),
        ),
    ]