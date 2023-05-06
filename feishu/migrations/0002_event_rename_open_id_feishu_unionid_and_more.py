# Generated by Django 4.1.3 on 2023-04-21 05:33

from django.db import migrations, models
import utils.utils_time


class Migration(migrations.Migration):

    dependencies = [
        ('feishu', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('eventid', models.TextField(verbose_name='事件唯一标识')),
                ('create_time', models.BigIntegerField(default=utils.utils_time.get_timestamp, verbose_name='创建时间')),
            ],
        ),
        migrations.RenameField(
            model_name='feishu',
            old_name='open_id',
            new_name='unionid',
        ),
        migrations.RemoveField(
            model_name='feishu',
            name='union_id',
        ),
        migrations.AddField(
            model_name='feishu',
            name='openid',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='feishu',
            name='userid',
            field=models.TextField(default=''),
        ),
    ]