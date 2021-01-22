from django.contrib.auth import get_user_model
from django.db import models
import timezone


User = get_user_model()


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


class MobileProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    laundry_preferences = models.ManyToManyField(LaundryRoom)
    dining_preferences = models.ManyToManyField(DiningVenue)


class SchoolProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    school_name = models.CharField(max_length=255)
    degree_name = models.CharField(max_length=255)
    major_name = models.CharField(max_length=255)
    expected_graduation = models.DateField(default=timezone.now)




class Course(models.Model):



# TODO: dining balance/transactions
