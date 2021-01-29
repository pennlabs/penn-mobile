from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

# TODO: dining balance/transactions
# TODO: Move LaundryRoom + Dining Venue to different django apps
class LaundryRoom(models.Model):
    # TODO: information about the laundry room
    pass


class DiningVenue(models.Model):
    pass


class NotificationToken(models.Model):
    KIND_IOS = "IOS"
    KIND_ANDROID = "ANDROID"
    KIND_OPTIONS = ((KIND_IOS, "iOS"), (KIND_ANDROID, "Android"))

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.CharField(max_length=7, choices=KIND_OPTIONS, default=KIND_IOS)
    dev = models.BooleanField(default=False)
    token = models.CharField(max_length=255)


class Degree(models.Model):
    school_name = models.CharField(max_length=255)
    degree_name = models.CharField(max_length=255)
    major_name = models.CharField(max_length=255)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    expected_graduation = models.DateField(null=True, blank=True)
    degrees = models.ManyToManyField(Degree, blank=True)

    # TODO: Adding serializers + correct models for this in subsequent updates
    laundry_preferences = models.ManyToManyField(LaundryRoom, blank=True)
    dining_preferences = models.ManyToManyField(DiningVenue, blank=True)

    # faculty used?
    # work on laundry, dining, and privacy
