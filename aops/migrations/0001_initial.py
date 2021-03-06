# Generated by Django 3.0.3 on 2020-09-17 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('year', models.PositiveIntegerField()),
                ('session', models.CharField(choices=[('A', 'A'), ('B', 'B')], max_length=20)),
                ('difficulty', models.PositiveIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('answer', models.CharField(blank=True, max_length=128, null=True)),
                ('note', models.CharField(blank=True, max_length=256)),
                ('category', models.ManyToManyField(related_name='problems', to='aops.Category')),
                ('topic', models.ManyToManyField(related_name='problems', to='aops.Topic')),
            ],
        ),
    ]
