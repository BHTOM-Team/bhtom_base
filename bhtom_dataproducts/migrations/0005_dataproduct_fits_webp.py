# Generated by Django 4.0.4 on 2024-07-03 15:47

import bhtom_base.bhtom_dataproducts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bhtom_dataproducts', '0004_remove_reduceddatum_match_distans_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataproduct',
            name='fits_webp',
            field=models.FileField(default='', null=True, upload_to=bhtom_base.bhtom_dataproducts.models.webp_data_path),
        ),
    ]