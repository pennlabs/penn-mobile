import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from games.models import Game, LeaderboardEntry
from games.serializers import GameDetailSerializer, GameSerializer


User = get_user_model()

DATE = datetime.date(2024, 3, 15)
BOARD = [["a", "b", "c", "d", "e"]] * 5
POSSIBLE_WORDS = ["cat", "dog", "fog", "log", "lag"]
SEED = "garden"


class TestGameModel(TestCase):
    def test_str_representation(self):
        game = Game.objects.create(date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED)
        self.assertEqual(str(DATE), str(game))

    def test_get_today_returns_todays_game(self):
        game = Game.objects.create(
            date=timezone.localdate(), board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED
        )
        self.assertEqual(game, Game.get_today())

    def test_get_today_returns_none_when_no_game(self):
        self.assertIsNone(Game.get_today())

    def test_get_today_ignores_other_dates(self):
        Game.objects.create(date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED)
        self.assertIsNone(Game.get_today())

    def test_freqs_field_round_trips(self):
        freqs = {"3": 10, "4": 8, "5": 5, "6": 2, "7": 1, "8": 0}
        game = Game.objects.create(
            date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED, freqs=freqs
        )
        game.refresh_from_db()
        self.assertEqual(freqs, game.freqs)

    def test_freqs_defaults_to_empty_dict(self):
        game = Game.objects.create(date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED)
        self.assertEqual({}, game.freqs)


class TestLeaderboardEntryModel(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "pass")
        self.user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "pass")
        self.game = Game.objects.create(
            date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED
        )

    def test_create_entry_stores_all_fields(self):
        entry = LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, words_found=3
        )
        self.assertEqual(300, entry.score)
        self.assertEqual(3, entry.words_found)
        self.assertEqual(self.game, entry.game)
        self.assertEqual(self.user1, entry.user)
        self.assertIsNotNone(entry.submitted_at)

    def test_unique_constraint_same_user_same_game(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=300, words_found=3)
        with self.assertRaises(IntegrityError):
            LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=400, words_found=4)

    def test_different_users_same_game_allowed(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=300, words_found=3)
        LeaderboardEntry.objects.create(game=self.game, user=self.user2, score=400, words_found=4)
        self.assertEqual(2, LeaderboardEntry.objects.count())

    def test_same_user_different_games_allowed(self):
        game2 = Game.objects.create(
            date=datetime.date(2024, 3, 16), board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED
        )
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=300, words_found=3)
        LeaderboardEntry.objects.create(game=game2, user=self.user1, score=400, words_found=4)
        self.assertEqual(2, LeaderboardEntry.objects.count())

    def test_default_ordering_by_score_descending(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=200, words_found=2)
        LeaderboardEntry.objects.create(game=self.game, user=self.user2, score=500, words_found=5)
        entries = list(LeaderboardEntry.objects.all())
        self.assertEqual(500, entries[0].score)
        self.assertEqual(200, entries[1].score)

    def test_tiebreaker_fewer_words_ranks_higher(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=300, words_found=5)
        LeaderboardEntry.objects.create(game=self.game, user=self.user2, score=300, words_found=2)
        entries = list(LeaderboardEntry.objects.all())
        self.assertEqual(self.user2, entries[0].user)
        self.assertEqual(2, entries[0].words_found)

    def test_cascade_delete_on_game_delete(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=300, words_found=3)
        self.game.delete()
        self.assertEqual(0, LeaderboardEntry.objects.count())

    def test_cascade_delete_on_user_delete(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=300, words_found=3)
        self.user1.delete()
        self.assertEqual(0, LeaderboardEntry.objects.count())


class TestGameSerializer(TestCase):
    def setUp(self):
        self.game = Game.objects.create(
            date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED,
            freqs={"3": 5, "4": 3},
        )

    def test_public_serializer_exposes_expected_fields(self):
        data = GameSerializer(self.game).data
        self.assertIn("date", data)
        self.assertIn("board", data)
        self.assertIn("possible_words", data)

    def test_public_serializer_hides_seed_and_freqs(self):
        data = GameSerializer(self.game).data
        self.assertNotIn("seed", data)
        self.assertNotIn("freqs", data)

    def test_detail_serializer_exposes_seed_and_freqs(self):
        data = GameDetailSerializer(self.game).data
        self.assertIn("seed", data)
        self.assertIn("freqs", data)
        self.assertEqual(SEED, data["seed"])
        self.assertEqual({"3": 5, "4": 3}, data["freqs"])
