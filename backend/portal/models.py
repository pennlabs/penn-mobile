from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class TargetPopulation(models.Model):
    KIND_SCHOOL = "SCHOOL"
    KIND_YEAR = "YEAR"
    KIND_MAJOR = "MAJOR"
    KIND_DEGREE = "DEGREE"
    KIND_OPTIONS = (
        (KIND_SCHOOL, "School"),
        (KIND_YEAR, "Year"),
        (KIND_MAJOR, "Major"),
        (KIND_DEGREE, "Degree"),
    )

    kind = models.CharField(max_length=10, choices=KIND_OPTIONS, default=KIND_SCHOOL)
    population = models.CharField(max_length=255)

    def __str__(self):
        return self.population


class Poll(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_REVISION = "REVISION"
    STATUS_APPROVED = "APPROVED"

    STATUS_OPTIONS = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_REVISION, "Revision"),
        (STATUS_APPROVED, "Approved"),
    )

    club_code = models.CharField(max_length=255, blank=True)
    question = models.CharField(max_length=255)
    created_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_OPTIONS, default=STATUS_DRAFT)
    multiselect = models.BooleanField(default=False)
    club_comment = models.CharField(max_length=255, null=True, blank=True)
    admin_comment = models.CharField(max_length=255, null=True, blank=True)
    target_populations = models.ManyToManyField(TargetPopulation, blank=True)

    def __str__(self):
        return f"{self.id} - {self.club_code} - {self.question}"


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice = models.CharField(max_length=255)
    vote_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.poll.id} - Option - {self.choice}"


class PollVote(models.Model):
    id_hash = models.CharField(max_length=255, blank=True)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    poll_options = models.ManyToManyField(PollOption)
    created_date = models.DateTimeField(default=timezone.now)
    target_populations = models.ManyToManyField(TargetPopulation, blank=True)


class Post(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_REVISION = "REVISION"
    STATUS_APPROVED = "APPROVED"

    STATUS_OPTIONS = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_REVISION, "Revision"),
        (STATUS_APPROVED, "Approved"),
    )

    club_code = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    post_url = models.URLField(null=True)
    # image = models.ImageField(upload_to="portal/images", null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField()
    status = models.CharField(max_length=30, choices=STATUS_OPTIONS, default=STATUS_DRAFT)
    club_comment = models.CharField(max_length=255, null=True, blank=True)
    admin_comment = models.CharField(max_length=255, null=True, blank=True)
    target_populations = models.ManyToManyField(TargetPopulation, blank=True)

    def __str__(self):
        return f"{self.id} - {self.club_code} - {self.title}"
