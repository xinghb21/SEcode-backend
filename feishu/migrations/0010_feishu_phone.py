# Generated by Django 4.1.3 on 2023-05-16 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feishu', '0009_alter_eventexception_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='feishu',
            name='phone',
            field=models.TextField(default=''),
        ),
    ]