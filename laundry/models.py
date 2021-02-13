import uuid

from django.db import models


class LaundrySnapshot(models.Model):
    hall_id = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    available_washers = models.IntegerField()
    available_dryers = models.IntegerField()
    total_washers = models.IntegerField()
    total_dryers = models.IntegerField()


class LaundryRoom(models.Model):
    hall_id = models.IntegerField(default=0)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4)

    def __str__(self):
        return f"{self.hall_id}-{self.name}"
