from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from portal.models import Poll, Post


User = get_user_model()


class Event(models.Model):
    TYPE_PENN_TODAY = "PENN TODAY"
    TYPE_VENTURE_LAB = "VENTURE LAB"
    TYPE_PENN_ENGINEERING = "PENN ENGINEERING"
    TYPE_RODIN_COLLEGE_HOUSE = "RODIN COLLEGE HOUSE"

    TYPE_CHOICES = (
        (TYPE_PENN_TODAY, "Penn Today"),
        (TYPE_VENTURE_LAB, "Venture Lab"),
        (TYPE_PENN_ENGINEERING, "Penn Engineering"),
        (TYPE_RODIN_COLLEGE_HOUSE, "Rodin College House"),
    )

    event_type = models.CharField(max_length=63, choices=TYPE_CHOICES, 
                                  default=None, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    website = models.URLField(max_length=255, null=True, blank=True)


class HomePageOrder(models.Model):
    cell = models.CharField(max_length=255)
    rank = models.IntegerField()

    def __str__(self):
        return self.cell


class FitnessRoom(models.Model):
    name = models.CharField(max_length=255)
    image_url = models.URLField()

    def __str__(self):
        return str(self.name)


class FitnessSnapshot(models.Model):
    room = models.ForeignKey(FitnessRoom, on_delete=models.CASCADE, null=True)
    date = models.DateTimeField(default=timezone.now)
    count = models.IntegerField()
    capacity = models.FloatField(null=True)

    def __str__(self):
        return f"Room Name: {self.room.name} | {self.date.date()}"


class AnalyticsEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    cell_type = models.CharField(max_length=255)
    index = models.IntegerField(default=0)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, null=True)
    is_interaction = models.BooleanField(default=False)
    data = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"{self.cell_type}-{self.user.username}"


class CalendarEvent(models.Model):
    event = models.CharField(max_length=255)
    date = models.CharField(max_length=50, null=True, blank=True)
    # NOTE: This is bad practice, though is necessary for the time being
    # since frontends use the string date field
    date_obj = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.date}-{self.event}"
