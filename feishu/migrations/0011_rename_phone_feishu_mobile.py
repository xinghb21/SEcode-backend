# Generated by Django 4.1.3 on 2023-05-16 08:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feishu', '0010_feishu_phone'),
    ]

    operations = [
        migrations.RenameField(
            model_name='feishu',
            old_name='phone',
            new_name='mobile',
        ),
    ]
