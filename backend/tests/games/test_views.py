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
    """Tests GET /games/today/"""

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
        response = self.client.get("/games/today/")
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
        response = self.client.get("/games/today/")
        self.assertEqual(404, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_get_today_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/games/today/")
        self.assertEqual(403, response.status_code)


class TestGameByDateView(TestCase):
    """Tests GET /games/<date>/"""

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
        response = self.client.get(f"/games/{DATE}/")
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
        response = self.client.get("/games/2000-01-01/")
        self.assertEqual(404, response.status_code)

    def test_get_game_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/games/{DATE}/")
        self.assertEqual(403, response.status_code)


class TestLeaderboardByDateView(TestCase):
    """Tests GET /games/<date>/leaderboard/"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        self.user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        self.client.force_authenticate(user=self.user1)
        self.game = Game.objects.create(
            date=DATE,
            board=BOARD,
            possible_words=POSSIBLE_WORDS,
            seed=SEED,
        )

    def test_get_leaderboard_empty(self):
        response = self.client.get(f"/games/{DATE}/leaderboard/")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual([], res_json)

    def test_get_leaderboard_with_entries(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=300, words_found=3)
        LeaderboardEntry.objects.create(game=self.game, user=self.user2, score=500, words_found=5)
        response = self.client.get(f"/games/{DATE}/leaderboard/")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        entry = res_json[0]
        self.assertIn("username", entry)
        self.assertIn("score", entry)
        self.assertIn("words_found", entry)
        self.assertIn("submitted_at", entry)

    def test_leaderboard_ordered_by_score_descending(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=300, words_found=3)
        LeaderboardEntry.objects.create(game=self.game, user=self.user2, score=500, words_found=5)
        response = self.client.get(f"/games/{DATE}/leaderboard/")
        res_json = json.loads(response.content)
        self.assertGreater(res_json[0]["score"], res_json[1]["score"])
        self.assertEqual(500, res_json[0]["score"])
        self.assertEqual(300, res_json[1]["score"])

    def test_leaderboard_tiebreaker_fewer_words_wins(self):
        LeaderboardEntry.objects.create(game=self.game, user=self.user1, score=400, words_found=5)
        LeaderboardEntry.objects.create(game=self.game, user=self.user2, score=400, words_found=3)
        response = self.client.get(f"/games/{DATE}/leaderboard/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        self.assertEqual("user2", res_json[0]["username"])
        self.assertEqual(3, res_json[0]["words_found"])

    def test_get_leaderboard_not_found(self):
        response = self.client.get("/games/2000-01-01/leaderboard/")
        self.assertEqual(404, response.status_code)

    def test_get_leaderboard_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/games/{DATE}/leaderboard/")
        self.assertEqual(403, response.status_code)


class TestSubmitScoreView(TestCase):
    """Tests POST /games/<date>/submit/"""

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

    def test_submit_score(self):
        payload = {"score": 300, "words_found": 3}
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(201, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("username", res_json)
        self.assertIn("score", res_json)
        self.assertIn("words_found", res_json)
        self.assertIn("submitted_at", res_json)
        self.assertEqual("user1", res_json["username"])
        self.assertEqual(300, res_json["score"])
        self.assertEqual(3, res_json["words_found"])
        self.assertEqual(1, LeaderboardEntry.objects.count())

    def test_submit_score_missing_words_found(self):
        payload = {"score": 300}
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_submit_score_missing_score(self):
        payload = {"words_found": 3}
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_submit_score_duplicate(self):
        payload = {"score": 300, "words_found": 3}
        self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)
        self.assertEqual(1, LeaderboardEntry.objects.count())

    def test_submit_score_game_not_found(self):
        payload = {"score": 300, "words_found": 3}
        response = self.client.post(
            "/games/2000-01-01/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(404, response.status_code)

    def test_submit_score_non_integer_score(self):
        payload = {"score": "abc", "words_found": 3}
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_submit_score_negative_score(self):
        payload = {"score": -1, "words_found": 3}
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_submit_score_negative_words_found(self):
        payload = {"score": 300, "words_found": -1}
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("error", res_json)

    def test_submit_score_zero_values(self):
        payload = {"score": 0, "words_found": 0}
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(201, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual(0, res_json["score"])
        self.assertEqual(0, res_json["words_found"])

    def test_submit_score_unauthenticated(self):
        self.client.force_authenticate(user=None)
        payload = {"score": 300, "words_found": 3}
        response = self.client.post(
            f"/games/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(403, response.status_code)


class TestValidateGameLogView(TestCase):
    """Tests POST /games/<date>/validate/"""

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

    def test_validate_valid_words(self):
        payload = {"words": ["cat", "dog"]}
        response = self.client.post(
            f"/games/{DATE}/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertTrue(res_json["valid"])

    def test_validate_empty_words_list(self):
        payload = {"words": []}
        response = self.client.post(
            f"/games/{DATE}/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertTrue(res_json["valid"])

    def test_validate_invalid_words(self):
        payload = {"words": ["cat", "xyz"]}
        response = self.client.post(
            f"/games/{DATE}/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertFalse(res_json["valid"])
        self.assertIn("invalid_words", res_json)
        self.assertIn("xyz", res_json["invalid_words"])

    def test_validate_duplicate_words(self):
        payload = {"words": ["cat", "cat"]}
        response = self.client.post(
            f"/games/{DATE}/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertFalse(res_json["valid"])
        self.assertIn("error", res_json)

    def test_validate_case_insensitive(self):
        payload = {"words": ["CAT", "Dog"]}
        response = self.client.post(
            f"/games/{DATE}/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertTrue(res_json["valid"])

    def test_validate_whitespace_padded_words(self):
        payload = {"words": ["  cat  ", " dog "]}
        response = self.client.post(
            f"/games/{DATE}/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertTrue(res_json["valid"])

    def test_validate_words_not_a_list(self):
        payload = {"words": "cat"}
        response = self.client.post(
            f"/games/{DATE}/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertFalse(res_json["valid"])
        self.assertIn("error", res_json)

    def test_validate_game_not_found(self):
        payload = {"words": ["cat"]}
        response = self.client.post(
            "/games/2000-01-01/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(404, response.status_code)

    def test_validate_unauthenticated(self):
        self.client.force_authenticate(user=None)
        payload = {"words": ["cat"]}
        response = self.client.post(
            f"/games/{DATE}/validate/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(403, response.status_code)
