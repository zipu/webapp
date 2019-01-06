# Generated by Django 2.1.4 on 2018-12-31 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maths', '0006_auto_20181231_1316'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='difficulty',
            field=models.CharField(choices=[('H', 'Hard'), ('M', 'Medium'), ('E', 'Easy'), ('N', 'None')], max_length=16),
        ),
    ]