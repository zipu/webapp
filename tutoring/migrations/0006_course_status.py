# Generated by Django 3.0.3 on 2020-10-01 00:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0005_auto_20200930_2317'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='status',
            field=models.BooleanField(default=True, verbose_name='진행상태'),
            preserve_default=False,
        ),
    ]
