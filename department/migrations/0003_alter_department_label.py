# Generated by Django 4.1.3 on 2023-04-11 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('department', '0002_department_label'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='label',
            field=models.TextField(default=''),
        ),
    ]