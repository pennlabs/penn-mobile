# Generated by Django 4.0.3 on 2022-03-21 01:06
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("user", "0005_auto_20211003_2240"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notificationtoken",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.CreateModel(
            name="NotificationSetting",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID",
                    ),
                ),
                (
                    "service",
                    models.CharField(
                        choices=[
                            ("CFA", "CFA"),
                            ("PENN_CLUBS", "Penn Clubs"),
                            ("PENN_BASICS", "Penn Basics"),
                            ("OHQ", "OHQ"),
                            ("PENN_COURSE_ALERT", "Penn Course Alert"),
                            ("PENN_COURSE_PLAN", "Penn Course Plan"),
                            ("PENN_COURSE_REVIEW", "Penn Course Review"),
                            ("PENN_MOBILE", "Penn Mobile"),
                            ("GSR_BOOKING", "GSR_BOOKING"),
                        ],
                        default="PENN_MOBILE",
                        max_length=30,
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                (
                    "token",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.notificationtoken",
                    ),
                ),
            ],
        ),
    ]
