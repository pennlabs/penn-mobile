from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from portal.models import Poll, Post


User = get_user_model()


class Event(models.Model):
    TYPE_PENN_TODAY = "PENN TODAY"
    TYPE_VENTURE_LAB = "VENTURE LAB"
    TYPE_PENN_ENGINEERING = "PENN ENGINEERING"
    TYPE_WHARTON = "WHARTON"
    TYPE_UNIVERSITY_LIFE = "UNIVERSITY_LIFE"
    TYPE_RODIN_COLLEGE_HOUSE = "RODIN COLLEGE HOUSE"
    TYPE_HARNWELL_COLLEGE_HOUSE = "HARNWELL COLLEGE HOUSE"
    TYPE_HARRISON_COLLEGE_HOUSE = "HARRISON COLLEGE HOUSE"
    TYPE_GUTMANN_COLLEGE_HOUSE = "GUTMANN COLLEGE HOUSE"
    TYPE_RADIAN_COLLEGE_HOUSE = "RADIAN COLLEGE HOUSE"
    TYPE_LAUDER_COLLEGE_HOUSE = "LAUDER COLLEGE HOUSE"
    TYPE_HILL_COLLEGE_HOUSE = "HILL COLLEGE HOUSE"
    TYPE_KCECH_COLLEGE_HOUSE = "KCECH COLLEGE HOUSE"
    TYPE_WARE_COLLEGE_HOUSE = "WARE COLLEGE HOUSE"
    TYPE_FH_COLLEGE_HOUSE = "FISHER HASSENFELD COLLEGE HOUSE"
    TYPE_RIEPE_COLLEGE_HOUSE = "RIEPE COLLEGE HOUSE"
    TYPE_DUBOIS_COLLEGE_HOUSE = "DU BOIS COLLEGE HOUSE"
    TYPE_GREGORY_COLLEGE_HOUSE = "GREGORY COLLEGE HOUSE"
    TYPE_STOUFFER_COLLEGE_HOUSE = "STOUFFER COLLEGE HOUSE"

    TYPE_CHOICES = (
        (TYPE_PENN_TODAY, "Penn Today"),
        (TYPE_VENTURE_LAB, "Venture Lab"),
        (TYPE_PENN_ENGINEERING, "Penn Engineering"),
        (TYPE_WHARTON, "Wharton"),
        (TYPE_UNIVERSITY_LIFE, "University Life"),
        (TYPE_RODIN_COLLEGE_HOUSE, "Rodin College House"),
        (TYPE_HARNWELL_COLLEGE_HOUSE, "Harnwell College House"),
        (TYPE_HARRISON_COLLEGE_HOUSE, "Harrison College House"),
        (TYPE_GUTMANN_COLLEGE_HOUSE, "Gutmann College House"),
        (TYPE_RADIAN_COLLEGE_HOUSE, "Radian College House"),
        (TYPE_LAUDER_COLLEGE_HOUSE, "Lauder College House"),
        (TYPE_HILL_COLLEGE_HOUSE, "Hill College HouseE"),
        (TYPE_KCECH_COLLEGE_HOUSE, "Kcech College House"),
        (TYPE_WARE_COLLEGE_HOUSE, "Ware College House"),
        (TYPE_FH_COLLEGE_HOUSE, "Fisher Hassenfeld College House"),
        (TYPE_RIEPE_COLLEGE_HOUSE, "Riepe College House"),
        (TYPE_DUBOIS_COLLEGE_HOUSE, "Du Bois College House"),
        (TYPE_GREGORY_COLLEGE_HOUSE, "Gregory College House"),
        (TYPE_STOUFFER_COLLEGE_HOUSE, "Stouffer College House"),
    )

    event_type: models.CharField = models.CharField(
        max_length=63, choices=TYPE_CHOICES, default=None, null=True, blank=True
    )
    name: models.CharField = models.CharField(max_length=255)
    description: models.TextField = models.TextField(null=True, blank=True)
    image_url: models.URLField = models.URLField(null=True, blank=True)
    start: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    end: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    location: models.CharField = models.CharField(max_length=255, null=True, blank=True)
    email: models.CharField = models.CharField(max_length=255, null=True, blank=True)
    website: models.URLField = models.URLField(max_length=255, null=True, blank=True)


class HomePageOrder(models.Model):
    cell: models.CharField = models.CharField(max_length=255)
    rank: models.IntegerField = models.IntegerField()

    def __str__(self) -> str:
        return self.cell


class FitnessRoom(models.Model):
    id: int
    name: models.CharField = models.CharField(max_length=255)
    image_url: models.URLField = models.URLField()

    def __str__(self) -> str:
        return str(self.name)


class FitnessSnapshot(models.Model):
    room: models.ForeignKey = models.ForeignKey(FitnessRoom, on_delete=models.CASCADE, null=True)
    date: models.DateTimeField = models.DateTimeField(default=timezone.now)
    count: models.IntegerField = models.IntegerField()
    capacity: models.FloatField = models.FloatField(null=True)

    def __str__(self) -> str:
        return f"Room Name: {self.room.name} | {self.date.date()}"


class AnalyticsEvent(models.Model):
    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at: models.DateTimeField = models.DateTimeField(default=timezone.now)
    cell_type: models.CharField = models.CharField(max_length=255)
    index: models.IntegerField = models.IntegerField(default=0)
    post: models.ForeignKey = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    poll: models.ForeignKey = models.ForeignKey(Poll, on_delete=models.CASCADE, null=True)
    is_interaction: models.BooleanField = models.BooleanField(default=False)
    data: models.CharField = models.CharField(max_length=255, null=True)

    def __str__(self) -> str:
        return f"{self.cell_type}-{self.user.username}"


class CalendarEvent(models.Model):
    event: models.CharField = models.CharField(max_length=255)
    date: models.CharField = models.CharField(max_length=50, null=True, blank=True)
    # NOTE: This is bad practice, though is necessary for the time being
    # since frontends use the string date field
    date_obj: models.DateTimeField = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.date}-{self.event}"
