# Generated by Django 2.0.6 on 2018-09-25 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tom_targets', '0003_auto_20180905_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='target',
            name='parallax',
            field=models.FloatField(blank=True, help_text='Parallax, in parallax seconds.', null=True, verbose_name='Parallax'),
        ),
    ]