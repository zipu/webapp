# Generated by Django 3.0.3 on 2020-10-04 23:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0012_auto_20201004_2344'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='address',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
