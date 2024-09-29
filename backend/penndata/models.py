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

    event_type = models.CharField(
        max_length=63, choices=TYPE_CHOICES, default=None, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
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



# Adding statistics tracking here
class GlobalStats(models.Model):
    stat_key = models.CharField(max_length=50, on_delete=models.CASCADE, 
                                null=False, blank=False)
    stat_value = models.CharField(max_length=50, on_delete=models.CASCADE, 
                                  null=False, blank=False)
    year = models.IntegerField()
    
    class Meta:
        unique_together = ("stat_key", "year")

    def __str__(self):
        return f"Global -- {self.stat_key}-{str(self.year)} : {self.stat_value}"
    
class IndividualStats(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stat_key = models.CharField(max_length=50, on_delete=models.CASCADE, 
                                null=False, blank=False)
    stat_value = models.CharField(max_length=50, on_delete=models.CASCADE, 
                                  null=False, blank=False)
    year = models.IntegerField()

    class Meta: 
        unique_together = ("stat_key", "year", "user")

    def __str__(self) -> str:
        return f"User: {self.user} -- {self.stat_key}-{str(self.year)} : {self.stat_value}"
    

    
