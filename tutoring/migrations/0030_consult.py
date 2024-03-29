# Generated by Django 4.1.3 on 2023-12-28 17:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0029_alter_financialitem_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='Consult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('tag', models.CharField(blank=True, max_length=100, null=True)),
                ('note', models.TextField()),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tutoring.student')),
            ],
        ),
    ]
