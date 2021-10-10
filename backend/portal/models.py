from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class TargetPopulation(models.Model):
    KIND_SCHOOL = "SCHOOL"
    KIND_YEAR = "YEAR"
    KIND_MAJOR = "MAJOR"
    KIND_OPTIONS = ((KIND_SCHOOL, "School"), (KIND_YEAR, "Year"), (KIND_MAJOR, "Major"))

    kind = models.CharField(max_length=10, choices=KIND_OPTIONS, default=KIND_SCHOOL)
    population = models.CharField(max_length=255)


class Poll(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)
    question = models.CharField(max_length=255)
    created_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField()
    approved = models.BooleanField(default=False)
    multiselect = models.BooleanField(default=False)
    user_comment = models.CharField(max_length=255, null=True, blank=True)
    admin_comment = models.CharField(max_length=255, null=True, blank=True)
    target_populations = models.ManyToManyField(TargetPopulation, blank=True)


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice = models.CharField(max_length=255)
    vote_count = models.IntegerField(default=0)


class PollVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    poll_options = models.ManyToManyField(PollOption)
    created_date = models.DateTimeField(default=timezone.now)
