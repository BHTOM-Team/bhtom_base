# Generated by Django 4.0.4 on 2024-08-02 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bhtom_dataproducts', '0005_dataproduct_fits_webp'),
    ]

    operations = [
        migrations.AddField(
            model_name='ccdphotjob',
            name='use_catalog',
            field=models.IntegerField(blank=True, default=39, null=True),
        ),
    ]
