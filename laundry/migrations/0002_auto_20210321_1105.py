# Generated by Django 3.1.7 on 2021-03-21 15:05

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("laundry", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="laundrysnapshot",
            name="date",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
