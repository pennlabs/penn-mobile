# Generated by Django 3.1.7 on 2021-03-13 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("laundry", "0001_initial"),
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="laundry_preferences",
            field=models.ManyToManyField(blank=True, to="laundry.LaundryRoom"),
        ),
    ]
