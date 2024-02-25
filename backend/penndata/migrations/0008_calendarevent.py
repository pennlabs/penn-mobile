# Generated by Django 4.2.9 on 2024-02-04 23:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("penndata", "0007_fitnessroom_image_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="CalendarEvent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("event", models.CharField(max_length=255)),
                ("date", models.CharField(blank=True, max_length=50, null=True)),
                ("date_obj", models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]