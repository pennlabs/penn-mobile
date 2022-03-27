from django.db import models
from django.utils import timezone


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
        return f"Room Name {self.room.name} | {self.date.date()}"
