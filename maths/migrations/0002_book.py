# Generated by Django 2.1.4 on 2018-12-28 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maths', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('course', models.CharField(choices=[('IBHL', 'IB HighLevel'), ('IBSL', 'IB Standard'), ('APAB', 'AP Calculus AB'), ('APBC', 'AP Calculus BC'), ('PC', 'Pre Calculus'), ('AL2', 'Algebra 2'), ('GEO', 'Geometry'), ('Y9', 'Year 9'), ('Y10', 'Year 10'), ('Y11', 'Year 11')], max_length=16)),
                ('file_location', models.FileField(upload_to='maths/books/')),
            ],
        ),
    ]
