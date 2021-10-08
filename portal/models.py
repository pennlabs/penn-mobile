from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class TargetPopulation(models.Model):
    population = models.CharField(max_length=255)


class Poll(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)
    question = models.CharField(max_length=255)
    image_url = models.URLField(null=True, blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField()
    approved = models.BooleanField(default=False)
    multiselect = models.BooleanField(default=False)
    user_comment = models.CharField(max_length=255, null=True, blank=True)
    admin_comment = models.CharField(max_length=255, null=True, blank=True)
    target_populations = models.ManyToManyField(TargetPopulation)


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice = models.CharField(max_length=255)


class PollVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    poll_options = models.ManyToManyField(PollOption)
    created_date = models.DateTimeField(default=timezone.now)


class PostAccount(models.Model):
    name = models.CharField(null=True)
    email = models.CharField(max_length=255, unique=True)
    encrypted_password = models.CharField(max_length=255)
    reset_password_token = models.CharField(max_length=255, null=True, unique=True)
    reset_password_token_sent_at = models.DateTimeField(null=True)
    sign_in_count = models.IntegerField(default=1)
    last_sign_in_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class Post(models.Model):
    account = models.ForeignKey(PostAccount, on_delete=models.CASCADE)
    source = models.CharField(null=True)
    title = models.CharField(null=True)
    subtitle = models.CharField(null=True)
    time_label = models.CharField(null=True)
    post_url = models.CharField(null=True)
    image_url = models.CharField()
    image_url_cropped = models.CharField()
    filters = models.BooleanField(default=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(nullable=False)
    approved = models.BooleanField(default=False)
    testers = models.BooleanField(default=False)
    emails = models.BooleanField(default=False)
    created_at = models.DateTimeField()
