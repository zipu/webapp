# Generated by Django 4.1.3 on 2022-12-22 18:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0056_remove_cashaccount_asset_delete_record_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ('-date',)},
        ),
    ]
