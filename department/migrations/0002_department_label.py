# Generated by Django 4.1.3 on 2023-04-11 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('department', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='label',
            field=models.TextField(default='[]'),
        ),
    ]
