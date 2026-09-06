import datetime
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from games.models import Game, LeaderboardEntry


User = get_user_model()

DATE = datetime.date(2024, 3, 15)
BOARD = [["a", "b", "c", "d"], ["e", "f", "g", "h"], ["i", "j", "k", "l"], ["m", "n", "o", "p"]]
POSSIBLE_WORDS = ["cat", "dog", "fog", "log", "lag"]
SEED = "abc123"


class TestTodayGameView(TestCase):
    """Tests GET /games/word-hunt/today/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.user)

    def test_get_today_game_exists(self):
        Game.objects.create(
            date=timezone.localdate(),
            board=BOARD,
            possible_words=POSSIBLE_WORDS,
            seed=SEED,
        )
        response = self.client.get("/games/word-hunt/today/")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("date", res_json)
        self.assertIn("board", res_json)
        self.assertIn("possible_words", res_json)
        self.assertNotIn("seed", res_json)
        self.assertEqual(str(timezone.localdate()), res_json["date"])
        self.assertEqual(BOARD, res_json["board"])
        self.assertEqual(POSSIBLE_WORDS, res_json["possible_words"])

    def test_get_today_game_not_found(self):
        response = self.client.get("/games/word-hunt/today/")
        self.assertEqual(404, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_get_today_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/games/word-hunt/today/")
        self.assertEqual(403, response.status_code)


class TestGameByDateView(TestCase):
    """Tests GET /games/word-hunt/<date>/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.user)
        self.game = Game.objects.create(
            date=DATE,
            board=BOARD,
            possible_words=POSSIBLE_WORDS,
            seed=SEED,
        )

    def test_get_game_by_date(self):
        response = self.client.get(f"/games/word-hunt/{DATE}/")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("date", res_json)
        self.assertIn("board", res_json)
        self.assertIn("possible_words", res_json)
        self.assertNotIn("seed", res_json)
        self.assertEqual(str(DATE), res_json["date"])
        self.assertEqual(BOARD, res_json["board"])
        self.assertEqual(POSSIBLE_WORDS, res_json["possible_words"])

    def test_get_game_by_date_not_found(self):
        response = self.client.get("/games/word-hunt/2000-01-01/")
        self.assertEqual(404, response.status_code)

    def test_get_game_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/games/word-hunt/{DATE}/")
        self.assertEqual(403, response.status_code)


class TestLeaderboardByDateView(TestCase):
    """Tests GET /games/word-hunt/<date>/leaderboard/"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        self.user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        self.user3 = User.objects.create_user("user3", "user3@seas.upenn.edu", "user3")
        self.client.force_authenticate(user=self.user1)
        self.game = Game.objects.create(
            date=DATE,
            board=BOARD,
            possible_words=POSSIBLE_WORDS,
            seed=SEED,
        )

    def create_entries(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=9
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user3, score=400, num_words_found=1
        )

    def test_get_leaderboard_empty(self):
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual([], res_json)

    def test_get_leaderboard_with_entries(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        entry = res_json[0]
        self.assertIn("name", entry)
        self.assertIn("score", entry)
        self.assertIn("num_words_found", entry)
        self.assertIn("submitted_at", entry)
        self.assertNotIn("username", entry)

    def test_leaderboard_ordered_by_score_descending(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")
        res_json = json.loads(response.content)
        self.assertGreater(res_json[0]["score"], res_json[1]["score"])
        self.assertEqual(500, res_json[0]["score"])
        self.assertEqual(300, res_json[1]["score"])

    def test_leaderboard_limit(self):
        self.create_entries()
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/?limit=2")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual([500, 400], [entry["score"] for entry in res_json])

    def test_leaderboard_limit_invalid(self):
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/?limit=-1")
        self.assertEqual(400, response.status_code)
        self.assertIn("error", json.loads(response.content))

    def test_leaderboard_sort_by_field(self):
        self.create_entries()
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/?sort=-num_words_found")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual([9, 5, 1], [entry["num_words_found"] for entry in res_json])

    def test_leaderboard_sort_ascending(self):
        self.create_entries()
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/?sort=score")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual([300, 400, 500], [entry["score"] for entry in res_json])

    def test_leaderboard_sort_invalid(self):
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/?sort=password")
        self.assertEqual(400, response.status_code)
        self.assertIn("error", json.loads(response.content))

    def test_leaderboard_ties_broken_by_submission_time(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=300, num_words_found=3
        )
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")
        res_json = json.loads(response.content)
        self.assertLess(res_json[0]["submitted_at"], res_json[1]["submitted_at"])

    def test_leaderboard_anonymous_by_default(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")
        self.assertIsNone(json.loads(response.content)[0]["name"])

    def test_leaderboard_shows_name_when_opted_in(self):
        self.user1.first_name, self.user1.last_name = "Ben", "Liu"
        self.user1.save()
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3, show_name=True
        )
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")
        self.assertEqual("Ben Liu", json.loads(response.content)[0]["name"])

    def test_leaderboard_opted_in_without_name_stays_anonymous(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3, show_name=True
        )
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")
        self.assertIsNone(json.loads(response.content)[0]["name"])

    def test_get_leaderboard_not_found(self):
        response = self.client.get("/games/word-hunt/2000-01-01/leaderboard/")
        self.assertEqual(404, response.status_code)

    def test_get_leaderboard_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")
        self.assertEqual(403, response.status_code)


class TestSubmitScoreView(TestCase):
    """Tests POST /games/word-hunt/<date>/submit/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        self.client.force_authenticate(user=self.user)
        self.game = Game.objects.create(
            date=DATE,
            board=BOARD,
            possible_words=POSSIBLE_WORDS,
            seed=SEED,
        )

    def test_submit_valid_words(self):
        payload = {"words": ["cat", "dog"]}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(201, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("name", res_json)
        self.assertIn("score", res_json)
        self.assertIn("num_words_found", res_json)
        self.assertIn("submitted_at", res_json)
        self.assertEqual(2, res_json["num_words_found"])
        self.assertEqual(1, LeaderboardEntry.objects.count())
        self.assertFalse(LeaderboardEntry.objects.get().show_name)

    def test_submit_opting_in_to_show_name(self):
        payload = {"words": ["cat"], "show_name": True}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(201, response.status_code)
        self.assertTrue(LeaderboardEntry.objects.get().show_name)

    def test_score_computed_from_word_lengths(self):
        payload = {"words": ["cat"]}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(201, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual((3 - 2) ** 2 * 100, res_json["score"])

    def test_submit_invalid_words_rejected(self):
        payload = {"words": ["cat", "notarealword"]}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)
        self.assertIn("invalid_words", res_json)
        self.assertIn("notarealword", res_json["invalid_words"])

    def test_submit_duplicate_words_rejected(self):
        payload = {"words": ["cat", "cat"]}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_submit_words_not_a_list(self):
        payload = {"words": "cat"}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_submit_duplicate_entry_rejected(self):
        payload = {"words": ["cat"]}
        self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)
        self.assertEqual(1, LeaderboardEntry.objects.count())

    def test_submit_game_not_found(self):
        payload = {"words": ["cat"]}
        response = self.client.post(
            "/games/word-hunt/2000-01-01/submit/",
            json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(404, response.status_code)

    def test_submit_unauthenticated(self):
        self.client.force_authenticate(user=None)
        payload = {"words": ["cat"]}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(403, response.status_code)
