from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from portal.models import Poll, Post


User = get_user_model()


class Event(models.Model):
    event_type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.URLField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    email = models.CharField(max_length=255)
    website = models.URLField(max_length=255, null=True)
    facebook = models.URLField(max_length=255, null=True)


class HomePageOrder(models.Model):
    cell = models.CharField(max_length=255)
    rank = models.IntegerField()

    def __str__(self):
        return self.cell


class FitnessRoom(models.Model):
    name = models.CharField(max_length=255)
    # TODO "portal/images" does not exist, add back images
    # image = models.ImageField(upload_to="portal/images", blank=False)

    def __str__(self):
        return str(self.name)


class FitnessSnapshot(models.Model):
    room = models.ForeignKey(FitnessRoom, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField(default=timezone.now)
    count = models.IntegerField()

    def __str__(self):
        return f"Room Name: {self.room.name} | {self.date.date()}"

class AnalyticsType(models.Model):
    name = models.CharField(max_length=255)
    data_str_required = models.BooleanField()
    data_num_required = models.BooleanField()

class AnalyticsEvent(models.Model):
    # TODO: would it be better to just have a type field, similar to that
    # of the NotificationSettings model, where we limit type
    # that way, we can get rid of the post/portal fields since this should be
    # more generic?
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.ForeignKey(AnalyticsType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    clicked = models.CharField(max_length=255)
    data_str = models.CharField(max_length=512, null=True)
    data_num = models.FloatField(null=True)

    def __str__(self):
        return f"{self.type.name}-{self.user.username}"
