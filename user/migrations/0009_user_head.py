# Generated by Django 4.1.3 on 2023-05-14 01:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_alter_user_apps'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='head',
            field=models.BooleanField(default=False),
        ),
    ]
