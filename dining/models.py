from django.db import models
from django.utils import timezone

from user.models import Profile


class Venue(models.Model):
    venue_id = models.IntegerField()
    image_url = models.URLField()

    def __str__(self):
        return str(self.venue_id)


class DiningPreference(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.profile} - {self.venue.venue_id}"


class DiningTransaction(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField()
    description = models.TextField()
    amount = models.FloatField()
    balance = models.FloatField(default=0)

    def __str__(self):
        return f"{self.profile} - {self.date} - {self.amount}"


class DiningBalance(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    dining_dollars = models.FloatField()
    swipes = models.IntegerField()
    guest_swipes = models.IntegerField()

    def __str__(self):
        return f"{self.profile} - {self.date}"
