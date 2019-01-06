# Generated by Django 2.1.4 on 2019-01-02 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maths', '0011_auto_20190102_1843'),
    ]

    operations = [
        migrations.CreateModel(
            name='Klass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name1', models.CharField(max_length=255)),
                ('pub_date', models.DateField()),
                ('course', models.CharField(choices=[('IBHL', 'IB HighLevel'), ('IBSL', 'IB Standard'), ('APAB', 'AP Calculus AB'), ('APBC', 'AP Calculus BC'), ('PreCal', 'Pre Calculus'), ('Algebra2', 'Algebra 2'), ('Geometry', 'Geometry'), ('Y9', 'Year 9'), ('Y10', 'Year 10'), ('Y11', 'Year 11'), ('etc', 'etc')], max_length=16)),
                ('status', models.BooleanField(default=True)),
                ('note', models.TextField(blank=True, max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Lecture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name2', models.CharField(max_length=255)),
                ('lecture_note', models.ManyToManyField(blank=True, related_name='lecture_note', to='maths.Document')),
                ('worksheet', models.ManyToManyField(blank=True, related_name='worksheet', to='maths.Document')),
            ],
        ),
        migrations.AddField(
            model_name='klass',
            name='lecture',
            field=models.ManyToManyField(to='maths.Lecture'),
        ),
    ]