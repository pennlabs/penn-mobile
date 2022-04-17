# Generated by Django 3.2.5 on 2021-09-07 01:42

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Poll",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("source", models.CharField(max_length=255)),
                ("question", models.CharField(max_length=255)),
                ("image_url", models.URLField(blank=True, null=True)),
                ("created_date", models.DateTimeField(default=django.utils.timezone.now)),
                ("expire_date", models.DateTimeField()),
                ("approved", models.BooleanField(default=False)),
                ("multiselect", models.BooleanField(default=False)),
                ("user_comment", models.CharField(blank=True, max_length=255, null=True)),
                ("admin_comment", models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="PollOption",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("choice", models.CharField(max_length=255)),
                (
                    "poll",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="portal.poll"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TargetPopulation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("population", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="PollVote",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("created_date", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "poll",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="portal.poll"
                    ),
                ),
                ("poll_options", models.ManyToManyField(to="portal.PollOption")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="poll",
            name="target_populations",
            field=models.ManyToManyField(to="portal.TargetPopulation"),
        ),
        migrations.AddField(
            model_name="poll",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
