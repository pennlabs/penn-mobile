from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from laundry.models import LaundryRoom
from penndata.models import FitnessRoom


User = get_user_model()


class NotificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, primary_key=True)

    class Meta:
        abstract = True


class IOSNotificationToken(NotificationToken):
    is_dev = models.BooleanField(default=False)


class AndroidNotificationToken(NotificationToken):
    pass


class NotificationService(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    enabled_users = models.ManyToManyField(User, blank=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    laundry_preferences = models.ManyToManyField(LaundryRoom, blank=True)
    fitness_preferences = models.ManyToManyField(FitnessRoom, blank=True)
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
