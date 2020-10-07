# Generated by Django 3.0.3 on 2020-09-29 11:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('startdate', models.DateField()),
                ('time', models.CharField(max_length=250)),
            ],
        ),
        migrations.CreateModel(
            name='Curriculum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('tution', models.IntegerField()),
                ('topics', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('wechat_id', models.CharField(max_length=64)),
                ('school', models.CharField(choices=[('SASPX', 'SASPX'), ('SASPD', 'SASPD'), ('BISSPD', 'BISSPD'), ('BISSPX', 'BISSPX'), ('SHID', 'SHID'), ('SCIS', 'SCIS'), ('YCIS', 'YCIS'), ('SSIS', 'SSIS'), ('한국학교', '한국학교')], max_length=64)),
                ('year', models.PositiveIntegerField()),
                ('status', models.BooleanField()),
                ('region', models.CharField(max_length=64)),
                ('note', models.CharField(blank=True, max_length=250, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tuition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('deposit', models.IntegerField()),
                ('note', models.CharField(blank=True, max_length=250, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tutoring.Student')),
            ],
        ),
        migrations.CreateModel(
            name='CourseDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('date', models.DateTimeField()),
                ('homework', models.BooleanField()),
                ('note', models.CharField(blank=True, max_length=128, null=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tutoring.Course')),
                ('students', models.ManyToManyField(to='tutoring.Student')),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='curriculum',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tutoring.Curriculum'),
        ),
    ]
