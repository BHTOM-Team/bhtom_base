# Generated by Django 4.0.4 on 2022-05-04 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bhtom_dataproducts', '0014_alter_reduceddatum_mjd'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reduceddatum',
            name='mjd',
            field=models.FloatField(default=59703.6193698374),
        ),
    ]