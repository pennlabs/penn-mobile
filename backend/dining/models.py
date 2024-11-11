from django.db import models
from django.db.models import (
    CharField,
    DateField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    ManyToManyField,
    URLField,
)
from django.utils import timezone


class Venue(models.Model):
    venue_id: IntegerField = models.IntegerField(primary_key=True)
    name: CharField = models.CharField(max_length=255, null=True)
    image_url: URLField = models.URLField()

    def __str__(self) -> str:
        return f"{self.name}-{str(self.venue_id)}"


class DiningItem(models.Model):
    item_id: IntegerField = models.IntegerField(primary_key=True)
    name: CharField = models.CharField(max_length=255)
    description: CharField = models.CharField(max_length=1000, blank=True)
    ingredients: CharField = models.CharField(max_length=1000, blank=True)  # comma separated list
    allergens: CharField = models.CharField(max_length=1000, blank=True)  # comma separated list
    nutrition_info: CharField = models.CharField(max_length=1000, blank=True)  # json string.
    # Technically, postgres supports json fields but that involves local postgres
    # instead of sqlite AND we don't need to query on this field

    def __str__(self) -> str:
        return f"{self.name}"


class DiningStation(models.Model):
    name: CharField = models.CharField(max_length=255)
    items: ManyToManyField = models.ManyToManyField(DiningItem)
    menu: ForeignKey = models.ForeignKey(
        "DiningMenu", on_delete=models.CASCADE, related_name="stations"
    )


class DiningMenu(models.Model):
    venue: ForeignKey = models.ForeignKey(Venue, on_delete=models.CASCADE)
    date: DateField = models.DateField(default=timezone.now)
    start_time: DateTimeField = models.DateTimeField()
    end_time: DateTimeField = models.DateTimeField()
    service: CharField = models.CharField(max_length=255)
