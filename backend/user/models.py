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

# class NotificationSetting(models.Model):
#     SERVICE_CFA = "CFA"
#     SERVICE_PENN_CLUBS = "PENN_CLUBS"
#     SERVICE_PENN_BASICS = "PENN_BASICS"
#     SERVICE_OHQ = "OHQ"
#     SERVICE_PENN_COURSE_ALERT = "PENN_COURSE_ALERT"
#     SERVICE_PENN_COURSE_PLAN = "PENN_COURSE_PLAN"
#     SERVICE_PENN_COURSE_REVIEW = "PENN_COURSE_REVIEW"
#     SERVICE_PENN_MOBILE = "PENN_MOBILE"
#     SERVICE_GSR_BOOKING = "GSR_BOOKING"
#     SERVICE_DINING = "DINING"
#     SERVICE_UNIVERSITY = "UNIVERSITY"
#     SERVICE_LAUNDRY = "LAUNDRY"
#     SERVICE_OPTIONS = (
#         (SERVICE_CFA, "CFA"),
#         (SERVICE_PENN_CLUBS, "Penn Clubs"),
#         (SERVICE_PENN_BASICS, "Penn Basics"),
#         (SERVICE_OHQ, "OHQ"),
#         (SERVICE_PENN_COURSE_ALERT, "Penn Course Alert"),
#         (SERVICE_PENN_COURSE_PLAN, "Penn Course Plan"),
#         (SERVICE_PENN_COURSE_REVIEW, "Penn Course Review"),
#         (SERVICE_PENN_MOBILE, "Penn Mobile"),
#         (SERVICE_GSR_BOOKING, "GSR Booking"),
#         (SERVICE_DINING, "Dining"),
#         (SERVICE_UNIVERSITY, "University"),
#         (SERVICE_LAUNDRY, "Laundry"),
#     )

    
#     service = models.CharField(max_length=30, choices=SERVICE_OPTIONS, default=SERVICE_PENN_MOBILE)
#     enabled = models.BooleanField(default=True)


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
