# Generated by Django 3.0.3 on 2020-09-29 11:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aops', '0002_problem_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='problem',
            options={'ordering': ('-id',)},
        ),
    ]
