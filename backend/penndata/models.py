from django.db import models


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
