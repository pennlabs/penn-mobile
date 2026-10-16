import math

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from presence.validators import validate_geofence, validate_opening_hours


User = get_user_model()


class Venue(models.Model):
    class Kind(models.TextChoices):
        GYM = "gym", "Gym"
        DINING = "dining", "Dining"
        LIBRARY = "library", "Library"
        OTHER = "other", "Other"

    venue_id = models.SlugField(max_length=64, primary_key=True)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.OTHER)
    geofence = models.JSONField(default=dict, blank=True)
    min_dwell_seconds = models.PositiveIntegerField(default=180, validators=[MinValueValidator(1)])
    exit_grace_seconds = models.PositiveIntegerField(default=120)
    max_accuracy_m = models.FloatField(default=50, validators=[MinValueValidator(1)])
    capacity = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    min_sample_size = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1)])
    calibration = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    opening_hours = models.JSONField(default=dict, blank=True)
    configuration_version = models.PositiveIntegerField(default=1, editable=False)
    dining_venue = models.OneToOneField(
        "dining.Venue",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="presence_venue",
    )
    fitness_rooms = models.ManyToManyField(
        "penndata.FitnessRoom", blank=True, related_name="presence_venues"
    )

    class Meta:
        ordering = ["venue_id"]

    def __str__(self):
        return self.venue_id

    def clean(self):
        super().clean()
        errors = {}
        for field, validator in (
            ("geofence", validate_geofence),
            ("opening_hours", validate_opening_hours),
        ):
            try:
                validator(getattr(self, field))
            except ValidationError as error:
                errors[field] = error.messages
        if self.enabled:
            for field in ("geofence", "opening_hours"):
                if not getattr(self, field):
                    errors[field] = "Enabled venues require a geofence and verified opening hours."
        if isinstance(self.max_accuracy_m, (int, float)) and not math.isfinite(self.max_accuracy_m):
            errors["max_accuracy_m"] = "Must be finite."
        if self.dining_venue_id is not None and self.kind != self.Kind.DINING:
            errors["dining_venue"] = "Only dining venues can reference a dining source."
        if errors:
            raise ValidationError(errors)


class PresenceOptIn(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="presence_opt_in")
    opted_in = models.BooleanField(default=False)
    policy_version = models.CharField(max_length=64, blank=True, default="")
    consented_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    revision = models.PositiveIntegerField(default=0)

    @property
    def has_current_consent(self):
        return self.opted_in and self.policy_version == settings.PRESENCE_PRIVACY_POLICY_VERSION

    @classmethod
    def is_opted_in(cls, user):
        return cls.objects.filter(
            user=user, opted_in=True, policy_version=settings.PRESENCE_PRIVACY_POLICY_VERSION
        ).exists()

    @classmethod
    def set_for_user(cls, user, opted_in, policy_version=""):
        from presence.consent import update_consent

        return update_consent(user, opted_in, policy_version)
