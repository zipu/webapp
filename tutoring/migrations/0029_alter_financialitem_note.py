# Generated by Django 4.1.3 on 2023-12-16 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0028_alter_financialcategory_level_financialitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financialitem',
            name='note',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
