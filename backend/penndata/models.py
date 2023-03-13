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
    capacity = models.FloatField()

    def __str__(self):
        return f"Room Name: {self.room.name} | {self.date.date()}"


class AnalyticsEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    cell_type = models.CharField(max_length=255)
    index = models.IntegerField(default=0)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, null=True)
    is_interaction = models.BooleanField(default=False)
    data = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"{self.cell_type}-{self.user.username}"