# Generated by Django 4.1.3 on 2023-04-15 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pending', '0003_alter_pending_asset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pending',
            name='asset',
            field=models.TextField(default='[]'),
        ),
    ]