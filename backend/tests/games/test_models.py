import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from games.models import Game, GameUser, LeaderboardEntry


User = get_user_model()

DATE = datetime.date(2024, 3, 15)
BOARD = [["a", "b", "c", "d", "e"]] * 5
POSSIBLE_WORDS = ["cat", "dog", "fog", "log", "lag"]
SEED = "garden"


class TestGameUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user1", "user1@seas.upenn.edu", "pass")

    def test_for_user_defaults_to_anonymized(self):
        game_user = GameUser.for_user(self.user)

        self.assertTrue(game_user.anonymized)
        self.assertEqual(self.user, game_user.user)

    def test_sync_from_platform_updates_demographics(self):
        with patch(
            "games.models.platform_student_attrs",
            return_value={"school": "SEAS", "major": "CIS", "graduation_year": 2026},
        ) as sync:
            game_user = GameUser.sync_from_platform(self.user)

        self.assertEqual(
            ("SEAS", "CIS", 2026), (game_user.school, game_user.major, game_user.graduation_year)
        )
        self.assertTrue(game_user.anonymized)
        sync.assert_called_once_with(self.user)


class TestLeaderboardEntryModel(TestCase):
    def test_same_user_cannot_submit_twice_for_game(self):
        user = User.objects.create_user("user1", "user1@seas.upenn.edu", "pass")
        game = Game.objects.create(date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED)
        LeaderboardEntry.objects.create(game=game, user=user, score=300, num_words_found=3)

        with self.assertRaises(IntegrityError):
            LeaderboardEntry.objects.create(game=game, user=user, score=400, num_words_found=4)
