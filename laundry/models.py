import uuid
from django.db import models


class LaundrySnapshot(models.Model):
    room = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    available_washers = models.IntegerField()
    available_dryers = models.IntegerField()
    total_washers = models.IntegerField()
    total_dryers = models.IntegerField()

class LaundryRoom(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    uiud = models.UUIDField(default=uuid.uuid4)
