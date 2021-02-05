from django.db import models


class LaundrySnapshot(models.Model):
    room = models.IntegerField()
    date = models.DateTimeField()
    available_washers = models.IntegerField()
    available_dryers = models.IntegerField()
    total_washers = models.IntegerField()
    total_dryers = models.IntegerField()
