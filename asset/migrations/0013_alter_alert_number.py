# Generated by Django 4.1.3 on 2023-05-08 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0012_alert'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='number',
            field=models.FloatField(default=0),
        ),
    ]