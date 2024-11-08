# Generated by Django 5.0.2 on 2024-11-08 18:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wrapped', '0012_globalstatkey_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalstatthrough',
            name='GlobalStatKey',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='wrapped.globalstatkey'),
        ),
        migrations.AlterField(
            model_name='page',
            name='global_stats',
            field=models.ManyToManyField(blank=True, through='wrapped.GlobalStatThrough', to='wrapped.globalstatkey'),
        ),
    ]
