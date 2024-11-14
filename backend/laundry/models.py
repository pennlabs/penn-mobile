import uuid

from django.db import models
from django.utils import timezone


class LaundryRoom(models.Model):
    hall_id: models.IntegerField = models.IntegerField(default=0)
    name: models.CharField = models.CharField(max_length=255)
    location: models.CharField = models.CharField(max_length=255)
    total_washers: models.IntegerField = models.IntegerField(default=0)
    total_dryers: models.IntegerField = models.IntegerField(default=0)

    # Each Laundry Room has a UUID that we need to
    # access Penn API laundry data
    uuid: models.UUIDField = models.UUIDField(default=uuid.uuid4)

    def __str__(self) -> str:
        return f"Hall No. {self.hall_id} | {self.name}"


class LaundrySnapshot(models.Model):
    room: models.ForeignKey = models.ForeignKey(LaundryRoom, on_delete=models.CASCADE, null=True)
    date: models.DateTimeField = models.DateTimeField(default=timezone.now)
    available_washers: models.IntegerField = models.IntegerField()
    available_dryers: models.IntegerField = models.IntegerField()

    def __str__(self) -> str:
        return f"Hall No. {self.room.hall_id} | {self.date.date()}"  # ignore: type[attr-defined]
