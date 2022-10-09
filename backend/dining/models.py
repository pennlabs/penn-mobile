from django.db import models
from django.utils import timezone


class Venue(models.Model):
    venue_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    image_url = models.URLField()

    def __str__(self):
        return f"{self.name}-{str(self.venue_id)}"


class DiningItem(models.Model):
    item_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    ingredients = models.CharField(max_length=255)


class DiningStation(models.Model):
    name = models.CharField(max_length=255)
    items = models.ManyToManyField(DiningItem)


class DiningMenu(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    stations = models.ManyToManyField(DiningStation)
    service = models.CharField(max_length=255)
