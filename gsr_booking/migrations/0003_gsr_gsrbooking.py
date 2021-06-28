# Generated by Django 3.1.7 on 2021-06-28 21:37

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_auto_20210324_1851"),
        ("gsr_booking", "0002_auto_20210129_1527"),
    ]

    operations = [
        migrations.CreateModel(
            name="GSR",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("lid", models.IntegerField()),
                ("gid", models.IntegerField()),
                ("rid", models.IntegerField()),
                ("name", models.CharField(max_length=255)),
                ("image_url", models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name="GSRBooking",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("booking_id", models.IntegerField()),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                ("size", models.IntegerField()),
                ("date", models.DateTimeField(default=django.utils.timezone.now)),
                ("start", models.DateTimeField(default=django.utils.timezone.now)),
                ("end", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_cancelled", models.BooleanField(default=False)),
                ("reminder_sent", models.BooleanField(default=False)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.profile"
                    ),
                ),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="gsr_booking.gsr"
                    ),
                ),
            ],
        ),
    ]
