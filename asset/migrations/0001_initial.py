# Generated by Django 4.1.7 on 2023-04-01 07:20

from django.db import migrations, models
import utils.utils_time


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('parent', models.BigIntegerField(default=0)),
                ('department', models.BigIntegerField()),
                ('name', models.CharField(max_length=100)),
                ('type', models.BooleanField(default=False)),
                ('number', models.IntegerField(default=1)),
                ('belonging', models.BigIntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('life', models.IntegerField(default=0)),
                ('create_time', models.BigIntegerField(default=utils.utils_time.get_timestamp)),
                ('description', models.TextField(default='')),
                ('additional', models.TextField(default='{}')),
                ('status', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'Asset',
            },
        ),
    ]