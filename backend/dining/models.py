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
    description = models.CharField(max_length=1000)
    ingredients = models.CharField(max_length=1000)  # comma separated list
    allergens = models.CharField(max_length=1000)  # comma separated list
    nutrition_info = models.CharField(max_length=1000)  # json string.
    # Technically, postgres supports json fields but that involves local postgres instead of sqlite AND we don't need to query on this field

    def __str__(self):
        return f"{self.name}"


class DiningStation(models.Model):
    name = models.CharField(max_length=255)
    items = models.ManyToManyField(DiningItem)
    menu = models.ForeignKey("DiningMenu", on_delete=models.CASCADE)

class DiningMenu(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    stations = models.ManyToManyField(DiningStation)
    service = models.CharField(max_length=255)
