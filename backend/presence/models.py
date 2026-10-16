from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Venue(models.Model):
    venue_id = models.SlugField(max_length=64, primary_key=True)
    name = models.CharField(max_length=255)
    geofence = models.JSONField()
    min_dwell_seconds = models.PositiveIntegerField(default=180)
    exit_grace_seconds = models.PositiveIntegerField(default=120)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    min_sample_size = models.PositiveIntegerField(default=5)
    calibration = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.venue_id


class PresenceOptIn(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="presence_opt_in")
    opted_in = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def is_opted_in(cls, user):
        opt_in = getattr(user, "presence_opt_in", None)
        return opt_in is not None and opt_in.opted_in

    @classmethod
    def set_for_user(cls, user, opted_in):
        opt_in, _ = cls.objects.update_or_create(user=user, defaults={"opted_in": opted_in})
        user.presence_opt_in = opt_in
        return opt_in
