import uuid

from django.db import models


class LaundryRoom(models.Model):
    hall_id = models.IntegerField(default=0)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    total_washers = models.IntegerField(default=0)
    total_dryers = models.IntegerField(default=0)

    # Each Laundry Room has a UUID that we need to
    # access Penn API laundry data
    uuid = models.UUIDField(default=uuid.uuid4)

    def __str__(self):
        return f"Hall No. {self.hall_id} | {self.name}"


class LaundrySnapshot(models.Model):
    room = models.ForeignKey(LaundryRoom, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField(auto_now_add=True)
    available_washers = models.IntegerField()
    available_dryers = models.IntegerField()

    def __str__(self):
        return f"Hall No. {self.room.hall_id} | {self.date.date()}"
