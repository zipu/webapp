# Generated by Django 2.1.4 on 2019-01-02 18:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maths', '0012_auto_20190102_1844'),
    ]

    operations = [
        migrations.RenameField(
            model_name='klass',
            old_name='name1',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='lecture',
            old_name='name2',
            new_name='name',
        ),
    ]