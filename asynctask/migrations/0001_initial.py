# Generated by Django 4.1.3 on 2023-05-15 05:19

from django.db import migrations, models
import django.db.models.deletion
import utils.utils_time


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('department', '0001_initial'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Async_import_export_task',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('create_time', models.FloatField(default=utils.utils_time.get_timestamp)),
                ('status', models.SmallIntegerField(default=3)),
                ('process_time', models.FloatField(default=0)),
                ('finish_time', models.FloatField(default=0)),
                ('type', models.SmallIntegerField(default=0)),
                ('file_path', models.CharField(blank=True, max_length=255, null=True)),
                ('pid', models.IntegerField(default=0)),
                ('process', models.IntegerField(default=0)),
                ('ids', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('entity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='department.entity')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='user.user')),
            ],
        ),
    ]
