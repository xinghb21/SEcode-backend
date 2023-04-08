# Generated by Django 4.1.7 on 2023-04-01 07:20

from django.db import migrations, models
import utils.utils_time


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Logs',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('entity', models.BigIntegerField(default=0)),
                ('content', models.TextField(default='{}')),
                ('time', models.BigIntegerField(default=utils.utils_time.get_timestamp)),
                ('type', models.IntegerField(default=1)),
            ],
            options={
                'db_table': 'Logs',
            },
        ),
    ]