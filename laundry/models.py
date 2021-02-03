from django.db import models


class LaundrySnapshot(models.Model):
    room = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now=True)
    available_washers = models.IntegerField(default=0)
    available_dryers = models.IntegerField(default=0)
    total_washers = models.IntegerField(default=0)
    total_dryers = models.IntegerField(default=0)
