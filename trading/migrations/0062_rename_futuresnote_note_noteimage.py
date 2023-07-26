# Generated by Django 4.1.3 on 2022-12-25 21:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0061_alter_futuresnote_date_alter_futuresnote_tags'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='FuturesNote',
            new_name='Note',
        ),
        migrations.CreateModel(
            name='NoteImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='Image.set_file_name')),
                ('note', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='trading.futuresstrategy', verbose_name='image')),
            ],
        ),
    ]