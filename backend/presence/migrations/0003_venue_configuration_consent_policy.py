import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dining", "0006_remove_diningmenu_stations_and_more"),
        ("penndata", "0012_alter_event_event_type"),
        ("presence", "0002_presenceoptin"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="venue",
            options={"ordering": ["venue_id"]},
        ),
        migrations.AddField(
            model_name="presenceoptin",
            name="consented_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="presenceoptin",
            name="policy_version",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="presenceoptin",
            name="revision",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="venue",
            name="configuration_version",
            field=models.PositiveIntegerField(default=1, editable=False),
        ),
        migrations.AddField(
            model_name="venue",
            name="dining_venue",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="presence_venue",
                to="dining.venue",
            ),
        ),
        migrations.AddField(
            model_name="venue",
            name="fitness_rooms",
            field=models.ManyToManyField(
                blank=True, related_name="presence_venues", to="penndata.fitnessroom"
            ),
        ),
        migrations.AddField(
            model_name="venue",
            name="kind",
            field=models.CharField(
                choices=[
                    ("gym", "Gym"),
                    ("dining", "Dining"),
                    ("library", "Library"),
                    ("other", "Other"),
                ],
                default="other",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="venue",
            name="max_accuracy_m",
            field=models.FloatField(
                default=50, validators=[django.core.validators.MinValueValidator(1)]
            ),
        ),
        migrations.AddField(
            model_name="venue",
            name="opening_hours",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="venue",
            name="capacity",
            field=models.PositiveIntegerField(
                blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)]
            ),
        ),
        migrations.AlterField(
            model_name="venue",
            name="geofence",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="venue",
            name="min_dwell_seconds",
            field=models.PositiveIntegerField(
                default=180, validators=[django.core.validators.MinValueValidator(1)]
            ),
        ),
        migrations.AlterField(
            model_name="venue",
            name="min_sample_size",
            field=models.PositiveIntegerField(
                default=5, validators=[django.core.validators.MinValueValidator(1)]
            ),
        ),
    ]
