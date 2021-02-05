from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


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
<<<<<<< HEAD
    # faculty used?
    # work on laundry, dining, and privacy
=======

    # TODO: Adding serializers + correct models for this in subsequent updates
    # add laundry and dining preferences

    # faculty used?
>>>>>>> master
