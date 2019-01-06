# Generated by Django 2.1.4 on 2019-01-06 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maths', '0017_auto_20190105_1654'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pastexampaper',
            name='course',
        ),
        migrations.RemoveField(
            model_name='pastexampaper',
            name='name',
        ),
        migrations.RemoveField(
            model_name='pastexampaper',
            name='school',
        ),
        migrations.RemoveField(
            model_name='pastexampaper',
            name='topic',
        ),
        migrations.AddField(
            model_name='pastexampaper',
            name='exam',
            field=models.CharField(choices=[('IB STANDARD', 'IBSL'), ('IB HIGHLEVEL', 'IBHL'), ('AP Calculus AB', 'APAB'), ('AP Calculus BC', 'APBC'), ('AP Statistics', 'AP STAT'), ('SAT Math', 'SAT'), ('SAT2 Math', 'SAT2')], default='IBSL', max_length=32),
        ),
        migrations.AddField(
            model_name='pastexampaper',
            name='pub_year',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='pastexampaper',
            name='paper',
            field=models.ManyToManyField(to='maths.Document'),
        ),
    ]
