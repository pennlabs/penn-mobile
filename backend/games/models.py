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
        attrs["schools"] = schools
    if majors := [m.get("name") for m in student.get("major") or [] if m.get("name")]:
        attrs["majors"] = majors
    if year := student.get("graduation_year"):
        attrs["graduation_year"] = year
    return attrs


class GameUser(User):
    show_name = models.BooleanField(default=False)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)

    @classmethod
    def for_user(cls, user, show_name=None, schools=None, majors=None, graduation_year=None):
        game_user = cls.objects.filter(pk=user.pk).first()
        if game_user is None:
            game_user = cls(user_ptr_id=user.pk, show_name=False)
            game_user.save_base(raw=True)
        updates = []
        if show_name is not None and game_user.show_name != show_name:
            game_user.show_name = show_name
            updates.append("show_name")
        if graduation_year is not None and game_user.graduation_year != graduation_year:
            game_user.graduation_year = graduation_year
            updates.append("graduation_year")
        if updates:
            game_user.save(update_fields=updates)
        if schools is not None:
            game_user.replace_tags(GameUserTag.SCHOOL, schools)
        if majors is not None:
            game_user.replace_tags(GameUserTag.MAJOR, majors)
        return game_user

    def replace_tags(self, kind, values):
        self.tags.filter(kind=kind).delete()
        GameUserTag.objects.bulk_create(
            [GameUserTag(game_user=self, kind=kind, value=value) for value in values]
        )

    @classmethod
    def sync_from_platform(cls, user, show_name=None):
        attrs = platform_student_attrs(user)
        if show_name is not None:
            attrs["show_name"] = show_name
        return cls.for_user(user, **attrs)


class GameUserTag(models.Model):
    SCHOOL = "school"
    MAJOR = "major"

    game_user = models.ForeignKey(GameUser, on_delete=models.CASCADE, related_name="tags")
    kind = models.CharField(max_length=16)
    value = models.CharField(max_length=255)

    class Meta:
        indexes = [models.Index(fields=["kind", "value"])]


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
