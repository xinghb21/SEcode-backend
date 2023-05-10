# Generated by Django 4.1.3 on 2023-05-03 12:05

from django.db import migrations, models
import utils.utils_time


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0007_alter_asset_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='renew_time',
            field=models.FloatField(default=utils.utils_time.get_timestamp, null=True),
        ),
    ]
