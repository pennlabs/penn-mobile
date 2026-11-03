import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from games.models import Game, GameUser, LeaderboardEntry
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

    def test_word_length_freq_field_round_trips(self):
        freqs = {"3": 10, "4": 8, "5": 5, "6": 2, "7": 1, "8": 0}
        game = Game.objects.create(
            date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED, word_length_freq=freqs
        )
        game.refresh_from_db()
        self.assertEqual(freqs, game.word_length_freq)

    def test_word_length_freq_defaults_to_empty_dict(self):
        game = Game.objects.create(date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED)
        self.assertEqual({}, game.word_length_freq)


class TestGameUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user1", "user1@seas.upenn.edu", "pass")

    def test_for_user_creates_row_for_existing_user(self):
        game_user = GameUser.for_user(self.user)
        self.assertEqual(self.user, game_user.user)
        self.assertFalse(game_user.show_name)
        self.assertEqual(1, User.objects.filter(pk=self.user.pk).count())
        self.assertEqual(1, GameUser.objects.filter(user=self.user).count())

    def test_for_user_updates_show_name(self):
        GameUser.for_user(self.user, show_name=True)
        self.assertTrue(GameUser.objects.get(user=self.user).show_name)
        GameUser.for_user(self.user, show_name=False)
        self.assertFalse(GameUser.objects.get(user=self.user).show_name)

    def test_for_user_leaves_show_name_when_omitted(self):
        GameUser.for_user(self.user, show_name=True)
        GameUser.for_user(self.user)
        self.assertTrue(GameUser.objects.get(user=self.user).show_name)

    def test_for_user_stores_school_and_year(self):
        GameUser.for_user(self.user, schools=["SEAS"], majors=["CIS"], graduation_year=2026)
        game_user = GameUser.objects.get(user=self.user)
        self.assertEqual(
            ["SEAS"], list(game_user.tags.filter(kind="school").values_list("value", flat=True))
        )
        self.assertEqual(
            ["CIS"], list(game_user.tags.filter(kind="major").values_list("value", flat=True))
        )
        self.assertEqual(2026, game_user.graduation_year)


class TestLeaderboardEntryModel(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "pass")
        self.user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "pass")
        self.game = Game.objects.create(
            date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED
        )

    def test_create_entry_stores_all_fields(self):
        entry = LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        self.assertEqual(300, entry.score)
        self.assertEqual(3, entry.num_words_found)
        self.assertEqual(self.game, entry.game)
        self.assertEqual(self.user1, entry.user)
        self.assertIsNotNone(entry.submitted_at)

    def test_unique_constraint_same_user_same_game(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        with self.assertRaises(IntegrityError):
            LeaderboardEntry.objects.create(
                game=self.game, user=self.user1, score=400, num_words_found=4
            )

    def test_different_users_same_game_allowed(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=400, num_words_found=4
        )
        self.assertEqual(2, LeaderboardEntry.objects.count())

    def test_same_user_different_games_allowed(self):
        game2 = Game.objects.create(
            date=datetime.date(2024, 3, 16), board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(game=game2, user=self.user1, score=400, num_words_found=4)
        self.assertEqual(2, LeaderboardEntry.objects.count())

    def test_default_ordering_by_score_descending(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=200, num_words_found=2
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        entries = list(LeaderboardEntry.objects.all())
        self.assertEqual(500, entries[0].score)
        self.assertEqual(200, entries[1].score)

    def test_cascade_delete_on_game_delete(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        self.game.delete()
        self.assertEqual(0, LeaderboardEntry.objects.count())

    def test_cascade_delete_on_user_delete(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        self.user1.delete()
        self.assertEqual(0, LeaderboardEntry.objects.count())


class TestGameSerializer(TestCase):
    def setUp(self):
        self.game = Game.objects.create(
            date=DATE,
            board=BOARD,
            possible_words=POSSIBLE_WORDS,
            seed=SEED,
            word_length_freq={"3": 5, "4": 3},
        )

    def test_public_serializer_exposes_expected_fields(self):
        data = GameSerializer(self.game).data
        self.assertIn("date", data)
        self.assertIn("board", data)
        self.assertIn("possible_words", data)

    def test_public_serializer_hides_seed_and_word_length_freq(self):
        data = GameSerializer(self.game).data
        self.assertNotIn("seed", data)
        self.assertNotIn("word_length_freq", data)

    def test_detail_serializer_exposes_seed_and_word_length_freq(self):
        data = GameDetailSerializer(self.game).data
        self.assertIn("seed", data)
        self.assertIn("word_length_freq", data)
        self.assertEqual(SEED, data["seed"])
        self.assertEqual({"3": 5, "4": 3}, data["word_length_freq"])
