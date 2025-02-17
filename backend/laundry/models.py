from django.db import models
from django.utils import timezone


class LaundryRoom(models.Model):
    room_id = models.IntegerField(default=0, unique=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    location_id = models.IntegerField(default=0)
    total_washers = models.IntegerField(default=0)
    total_dryers = models.IntegerField(default=0)

    def __str__(self):
        return f"Room {self.name} | {self.location}"


class LaundrySnapshot(models.Model):
    room = models.ForeignKey(LaundryRoom, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField(default=timezone.now)
    available_washers = models.IntegerField()
    available_dryers = models.IntegerField()

    def __str__(self):
        return f"Room {self.room.name} | {self.date.date()}"
