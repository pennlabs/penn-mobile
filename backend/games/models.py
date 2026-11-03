from accounts.ipc import authenticated_request
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


def platform_student_attrs(user):
    if getattr(user, "accesstoken", None) is None:
        return {}
    response = authenticated_request(user, "GET", "https://platform.pennlabs.org/accounts/me/")
    if getattr(response, "status_code", None) != 200:
        return {}
    student = response.json().get("student") or {}
    attrs = {}
    if schools := [s.get("name") for s in student.get("school") or [] if s.get("name")]:
        attrs["school"] = schools[0]
    if majors := [m.get("name") for m in student.get("major") or [] if m.get("name")]:
        attrs["major"] = majors[0]
    if year := student.get("graduation_year"):
        attrs["graduation_year"] = year
    return attrs


class GameUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="gameuser")
    anonymized = models.BooleanField(default=True)
    school = models.CharField(max_length=255, blank=True)
    major = models.CharField(max_length=255, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)

    @classmethod
    def for_user(cls, user, anonymized=None):
        game_user, _ = cls.objects.get_or_create(user=user, defaults={"anonymized": True})
        if anonymized is not None and game_user.anonymized != anonymized:
            game_user.anonymized = anonymized
            game_user.save(update_fields=["anonymized"])
        return game_user

    @classmethod
    def sync_from_platform(cls, user):
        attrs = platform_student_attrs(user)
        game_user = cls.for_user(user)
        updates = []
        for field, value in attrs.items():
            if getattr(game_user, field) != value:
                setattr(game_user, field, value)
                updates.append(field)
        if updates:
            game_user.save(update_fields=updates)
        return game_user


class Game(models.Model):
    date = models.DateField(primary_key=True)
    board = models.JSONField()
    possible_words = models.JSONField()
    seed = models.CharField(max_length=32)
    word_length_freq = models.JSONField(default=dict)

    def __str__(self):
        return str(self.date)

    @classmethod
    def get_today(cls):
        return cls.objects.filter(date=timezone.localdate()).first()


class LeaderboardEntry(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="scores")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="word_hunt_scores")

    score = models.PositiveIntegerField(db_index=True)
    num_words_found = models.PositiveIntegerField()

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["game", "user"], name="unique_entry_per_user_per_game")
        ]
        ordering = ["-score"]
