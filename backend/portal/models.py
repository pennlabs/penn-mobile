import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.utils import timezone

from utils.email import get_backend_manager_emails, send_automated_email


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

    id: int
    kind: str = models.CharField(max_length=10, choices=KIND_OPTIONS, default=KIND_SCHOOL)
    population: str = models.CharField(max_length=255)

    def __str__(self):
        return self.population


class Content(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_REVISION = "REVISION"
    STATUS_APPROVED = "APPROVED"

    STATUS_OPTIONS = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_REVISION, "Revision"),
        (STATUS_APPROVED, "Approved"),
    )

    ACTION_REQUIRED_CONDITION = Q(expire_date__gt=timezone.now()) & Q(status=STATUS_DRAFT)

    id: int
    club_code: str = models.CharField(max_length=255, blank=True)
    created_date: datetime.datetime = models.DateTimeField(default=timezone.now)
    start_date: datetime.datetime = models.DateTimeField(default=timezone.now)
    expire_date: datetime.datetime = models.DateTimeField()
    status: str = models.CharField(max_length=30, choices=STATUS_OPTIONS, default=STATUS_DRAFT)
    club_comment: str = models.CharField(max_length=255, null=True, blank=True)
    admin_comment: str = models.CharField(max_length=255, null=True, blank=True)
    target_populations: models.ManyToManyField = models.ManyToManyField(
        TargetPopulation, blank=True
    )
    priority: int = models.IntegerField(default=0)
    creator: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        abstract = True

    def _get_email_subject(self) -> str:
        return f"[Portal] {self.__class__._meta.model_name.capitalize()} #{self.id}"

    def _on_create(self) -> None:
        send_automated_email.delay_on_commit(
            self._get_email_subject(),
            get_backend_manager_emails(),
            (
                f"A new {self.__class__._meta.model_name} for {self.club_code}"
                f"has been created by {self.creator}."
            ),
        )

    def _on_status_change(self) -> None:
        if email := getattr(self.creator, "email", None):
            send_automated_email.delay_on_commit(
                self._get_email_subject(),
                [email],
                f"Your {self.__class__._meta.model_name} status for {self.club_code} has been "
                + f"changed to {self.status}."
                + (
                    f"\n\nAdmin comment: {self.admin_comment}"
                    if self.admin_comment and self.status == self.STATUS_REVISION
                    else ""
                ),
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        prev = self.__class__.objects.filter(id=self.id).first()
        super().save(*args, **kwargs)
        if prev is None:
            self._on_create()
            return
        if self.status != prev.status:
            self._on_status_change()


class Poll(Content):
    question: str = models.CharField(max_length=255)
    multiselect: bool = models.BooleanField(default=False)

    def __str__(self):
        return self.question


class PollOption(models.Model):
    id: int
    poll: models.ForeignKey = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice: str = models.CharField(max_length=255)
    vote_count: int = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.poll.id} - Option - {self.choice}"


class PollVote(models.Model):
    id: int
    id_hash: str = models.CharField(max_length=255, blank=True)
    poll: models.ForeignKey = models.ForeignKey(Poll, on_delete=models.CASCADE)
    poll_options: models.ManyToManyField = models.ManyToManyField(PollOption)
    created_date: datetime.datetime = models.DateTimeField(default=timezone.now)
    target_populations: models.ManyToManyField = models.ManyToManyField(
        TargetPopulation, blank=True
    )


class Post(Content):
    title: str = models.CharField(max_length=255)
    subtitle: str = models.CharField(max_length=255)
    post_url: str = models.CharField(max_length=255, null=True, blank=True)
    image: models.ImageField = models.ImageField(upload_to="portal/images", null=True, blank=True)

    def __str__(self) -> str:
        return self.title
