from django.db import models
from django.utils import timezone


class Venue(models.Model):
    venue_id: models.IntegerField = models.IntegerField(primary_key=True)
    name: models.CharField = models.CharField(max_length=255, null=True)
    image_url: models.URLField = models.URLField()

    def __str__(self) -> str:
        return f"{self.name}-{str(self.venue_id)}"


class DiningItem(models.Model):
    item_id: models.IntegerField = models.IntegerField(primary_key=True)
    name: models.CharField = models.CharField(max_length=255)
    description: models.CharField = models.CharField(max_length=1000, blank=True)
    ingredients: models.CharField = models.CharField(
        max_length=1000, blank=True
    )  # comma separated list
    allergens: models.CharField = models.CharField(
        max_length=1000, blank=True
    )  # comma separated list
    nutrition_info: models.CharField = models.CharField(max_length=1000, blank=True)  # json string.
    # Technically, postgres supports json fields but that involves local postgres
    # instead of sqlite AND we don't need to query on this field

    def __str__(self) -> str:
        return f"{self.name}"


class DiningStation(models.Model):
    name: models.CharField = models.CharField(max_length=255)
    items: models.ManyToManyField = models.ManyToManyField(DiningItem)
    menu: models.ForeignKey = models.ForeignKey(
        "DiningMenu", on_delete=models.CASCADE, related_name="stations"
    )


class DiningMenu(models.Model):
    venue: models.ForeignKey = models.ForeignKey(Venue, on_delete=models.CASCADE)
    date: models.DateField = models.DateField(default=timezone.now)
    start_time: models.DateTimeField = models.DateTimeField()
    end_time: models.DateTimeField = models.DateTimeField()
    service: models.CharField = models.CharField(max_length=255)
