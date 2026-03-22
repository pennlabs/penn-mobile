from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class Game(models.Model):
    date = models.DateField(primary_key=True)
    board = models.JSONField()
    possible_words = models.JSONField()
    seed = models.CharField(max_length=32)
    freqs = models.JSONField(default=dict)

    def __str__(self):
        return str(self.date)

    @classmethod
    def get_today(cls):
        return cls.objects.filter(date=timezone.localdate()).first()


class LeaderboardEntry(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="scores")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="word_hunt_scores")

    score = models.PositiveIntegerField(db_index=True)
    words_found = models.PositiveIntegerField()

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["game", "user"], name="unique_entry_per_user_per_game")
        ]
        ordering = ["-score", "words_found", "submitted_at"]
