from django.db import models
from django.utils import timezone

from pennmobile.utils.time_formatter import stringify_date


class Venue(models.Model):
    venue_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    image_url = models.URLField()

    def __str__(self):
        return f"Venue-{self.name}-{str(self.venue_id)}"


class DiningItem(models.Model):
    item_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000)
    ingredients = models.CharField(max_length=1000)

    def __str__(self):
        return f"DiningItem-{self.name}-{str(self.item_id)}"


class DiningStation(models.Model):
    name = models.CharField(max_length=255)
    items = models.ManyToManyField(DiningItem)

    def __str__(self):
        return f"DiningStation-{self.name}"


class DiningMenu(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    stations = models.ManyToManyField(DiningStation)
    service = models.CharField(max_length=255)

    def __str__(self):
        return f"DiningMenu-{stringify_date(self.date)}-{self.service}"
