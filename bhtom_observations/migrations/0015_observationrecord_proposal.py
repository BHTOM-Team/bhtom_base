# Generated by Django 4.0.4 on 2023-04-03 15:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bhtom_observations', '0014_alter_proposal_facilities'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationrecord',
            name='proposal',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bhtom_observations.proposal'),
        ),
    ]
