from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from laundry.models import LaundryRoom


User = get_user_model()


class NotificationToken(models.Model):
    KIND_IOS = "IOS"
    KIND_ANDROID = "ANDROID"
    KIND_OPTIONS = ((KIND_IOS, "iOS"), (KIND_ANDROID, "Android"))

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.CharField(max_length=7, choices=KIND_OPTIONS, default=KIND_IOS)
    dev = models.BooleanField(default=False)
    token = models.CharField(max_length=255)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    laundry_preferences = models.ManyToManyField(LaundryRoom, blank=True)
    dining_preferences = models.ManyToManyField("dining.Venue", blank=True)

    def __str__(self):
        return str(self.user.username)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    This post_save hook triggers automatically when a User object is saved, and if no Profile
    object exists for that User, it will create one
    """
    Profile.objects.get_or_create(user=instance)
