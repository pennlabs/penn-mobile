from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class Poll(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)
    question = models.CharField(max_length=255)
    created_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField()
    approved = models.BooleanField(default=False)
    admin_comment = models.CharField(max_length=255, null=True)


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice = models.CharField(max_length=255)


class PollVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    poll_option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
