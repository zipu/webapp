# Generated by Django 3.0.3 on 2020-10-04 23:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutoring', '0011_auto_20201004_2234'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='course',
            options={'ordering': ('-status', '-startdate')},
        ),
        migrations.AlterField(
            model_name='lesson',
            name='homework',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='숙제'),
        ),
        migrations.AlterField(
            model_name='tuition',
            name='payment',
            field=models.CharField(choices=[('위챗페이', '위챗페이'), ('즈푸바오', '즈푸바오'), ('현금', '현금')], max_length=250),
        ),
    ]
