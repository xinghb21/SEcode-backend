# Generated by Django 4.1.3 on 2023-05-15 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('password', models.CharField(max_length=1000)),
                ('entity', models.BigIntegerField(default=0)),
                ('department', models.BigIntegerField(default=0)),
                ('identity', models.IntegerField(default=4)),
                ('lockedapp', models.CharField(default='000000001', max_length=9)),
                ('locked', models.BooleanField(default=False)),
                ('apps', models.TextField(default='{"data":[]}')),
                ('head', models.BooleanField(default=False)),
                ('hasasset', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'User',
            },
        ),
    ]
