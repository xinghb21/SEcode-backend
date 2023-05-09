# Generated by Django 4.1.3 on 2023-05-09 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0007_alter_asset_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='price',
            field=models.DecimalField(decimal_places=2, default=1000.0, max_digits=10),
        ),
    ]
