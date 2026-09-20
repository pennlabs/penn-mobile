import datetime
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from games.models import Game, GameUser, LeaderboardEntry


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
        self.assertIn("detail", res_json)

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

    def opt_in(self, *users):
        for user in users:
            GameUser.for_user(user, show_name=True)

    def create_entries(self):
        self.opt_in(self.user1, self.user2, self.user3)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=9
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user3, score=400, num_words_found=1
        )

    def leaderboard(self, query=""):
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/{query}")
        self.assertEqual(200, response.status_code)
        return json.loads(response.content)

    def test_get_leaderboard_empty(self):
        res_json = self.leaderboard()
        self.assertEqual([], res_json["leaderboard"])
        self.assertIsNone(res_json["me"])

    def test_get_leaderboard_with_entries(self):
        self.opt_in(self.user1, self.user2)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        res_json = self.leaderboard()
        self.assertEqual(2, len(res_json["leaderboard"]))
        entry = res_json["leaderboard"][0]
        self.assertIn("name", entry)
        self.assertIn("score", entry)
        self.assertIn("num_words_found", entry)
        self.assertIn("submitted_at", entry)
        self.assertIn("rank", entry)
        self.assertNotIn("username", entry)

    def test_leaderboard_ordered_by_score_descending(self):
        self.opt_in(self.user1, self.user2)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        res_json = self.leaderboard()
        self.assertGreater(res_json["leaderboard"][0]["score"], res_json["leaderboard"][1]["score"])
        self.assertEqual(500, res_json["leaderboard"][0]["score"])
        self.assertEqual(300, res_json["leaderboard"][1]["score"])

    def test_leaderboard_limit(self):
        self.create_entries()
        res_json = self.leaderboard("?limit=2")
        self.assertEqual([500, 400], [entry["score"] for entry in res_json["leaderboard"]])

    def test_leaderboard_limit_invalid(self):
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/?limit=-1")
        self.assertEqual(400, response.status_code)
        self.assertIn("detail", json.loads(response.content))

    def test_leaderboard_sort_by_field(self):
        self.create_entries()
        res_json = self.leaderboard("?sort=-num_words_found")
        self.assertEqual([9, 5, 1], [entry["num_words_found"] for entry in res_json["leaderboard"]])

    def test_leaderboard_sort_ascending(self):
        self.create_entries()
        res_json = self.leaderboard("?sort=score")
        self.assertEqual([300, 400, 500], [entry["score"] for entry in res_json["leaderboard"]])

    def test_leaderboard_sort_invalid(self):
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/?sort=password")
        self.assertEqual(400, response.status_code)
        self.assertIn("detail", json.loads(response.content))

    def test_leaderboard_ties_broken_by_submission_time(self):
        self.opt_in(self.user1, self.user2)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=300, num_words_found=3
        )
        res_json = self.leaderboard()
        self.assertLess(
            res_json["leaderboard"][0]["submitted_at"], res_json["leaderboard"][1]["submitted_at"]
        )
        self.assertEqual(1, res_json["leaderboard"][0]["rank"])
        self.assertEqual(1, res_json["leaderboard"][1]["rank"])

    def test_leaderboard_tied_rank_skips_next_number(self):
        self.opt_in(self.user1, self.user2, self.user3)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user3, score=500, num_words_found=5
        )
        ranks = [entry["rank"] for entry in self.leaderboard()["leaderboard"]]
        self.assertEqual([1, 1, 3], ranks)

    def test_opted_out_player_excluded_from_leaderboard(self):
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=900, num_words_found=3
        )
        self.opt_in(self.user2)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=100, num_words_found=3
        )
        res_json = self.leaderboard()
        self.assertEqual([100], [entry["score"] for entry in res_json["leaderboard"]])
        self.assertEqual(900, res_json["me"]["score"])
        self.assertEqual(1, res_json["me"]["rank"])

    def test_leaderboard_shows_name_when_opted_in(self):
        self.user1.first_name, self.user1.last_name = "Ben", "Liu"
        self.user1.save()
        GameUser.for_user(self.user1, show_name=True)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        self.assertEqual("Ben Liu", self.leaderboard()["leaderboard"][0]["name"])

    def test_leaderboard_opted_in_without_name_stays_anonymous(self):
        GameUser.for_user(self.user1, show_name=True)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=300, num_words_found=3
        )
        self.assertIsNone(self.leaderboard()["leaderboard"][0]["name"])

    def test_opted_out_viewer_sees_anonymized_names(self):
        self.user2.first_name, self.user2.last_name = "Ada", "Lovelace"
        self.user2.save()
        GameUser.for_user(self.user2, show_name=True)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        self.assertIsNone(self.leaderboard()["leaderboard"][0]["name"])

    def test_me_when_outside_top(self):
        self.create_entries()
        res_json = self.leaderboard("?limit=2")
        self.assertEqual([500, 400], [entry["score"] for entry in res_json["leaderboard"]])
        self.assertEqual(3, res_json["me"]["rank"])
        self.assertEqual(300, res_json["me"]["score"])

    def test_me_tied_with_last_visible_row(self):
        self.opt_in(self.user1, self.user2, self.user3)
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user1, score=400, num_words_found=4
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user2, score=500, num_words_found=5
        )
        LeaderboardEntry.objects.create(
            game=self.game, user=self.user3, score=400, num_words_found=4
        )
        res_json = self.leaderboard("?limit=2")
        self.assertEqual(2, res_json["me"]["rank"])
        self.assertEqual(2, res_json["leaderboard"][1]["rank"])

    def test_leaderboard_filter_by_school(self):
        GameUser.for_user(self.user1, show_name=True, schools=["SEAS"])
        GameUser.for_user(self.user2, show_name=True, schools=["Wharton", "SEAS"])
        GameUser.for_user(self.user3, show_name=True, schools=["Nursing"])
        self.create_entries()
        self.assertEqual(
            [500, 300],
            [entry["score"] for entry in self.leaderboard("?school=SEAS")["leaderboard"]],
        )

    def test_leaderboard_filter_by_year(self):
        GameUser.for_user(self.user1, show_name=True, graduation_year=2026)
        GameUser.for_user(self.user2, show_name=True, graduation_year=2027)
        GameUser.for_user(self.user3, show_name=True, graduation_year=2026)
        self.create_entries()
        self.assertEqual(
            [400, 300], [entry["score"] for entry in self.leaderboard("?year=2026")["leaderboard"]]
        )

    def test_leaderboard_filter_by_major(self):
        GameUser.for_user(self.user1, show_name=True, majors=["CIS"])
        GameUser.for_user(self.user2, show_name=True, majors=["FIN"])
        self.create_entries()
        self.assertEqual(
            [300], [entry["score"] for entry in self.leaderboard("?major=CIS")["leaderboard"]]
        )

    def test_leaderboard_year_invalid(self):
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/?year=abc")
        self.assertEqual(400, response.status_code)
        self.assertIn("detail", json.loads(response.content))

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
        self.assertFalse(GameUser.objects.get(user=self.user).show_name)

    def test_submit_opting_in_to_show_name(self):
        payload = {"words": ["cat"], "show_name": True}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(201, response.status_code)
        self.assertTrue(GameUser.objects.get(user=self.user).show_name)

    def test_show_name_is_user_level(self):
        self.user.first_name, self.user.last_name = "Ben", "Liu"
        self.user.save()
        game2 = Game.objects.create(
            date=datetime.date(2024, 3, 16),
            board=BOARD,
            possible_words=POSSIBLE_WORDS,
            seed=SEED,
        )
        self.client.post(
            f"/games/word-hunt/{DATE}/submit/",
            json.dumps({"words": ["cat"]}),
            content_type="application/json",
        )
        self.client.post(
            f"/games/word-hunt/{game2.date}/submit/",
            json.dumps({"words": ["dog"], "show_name": True}),
            content_type="application/json",
        )
        first = json.loads(self.client.get(f"/games/word-hunt/{DATE}/leaderboard/").content)
        self.assertEqual("Ben Liu", first["leaderboard"][0]["name"])

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
        self.assertIn("detail", res_json)
        self.assertIn("invalid_words", res_json)
        self.assertIn("notarealword", res_json["invalid_words"])

    def test_submit_duplicate_words_rejected(self):
        payload = {"words": ["cat", "cat"]}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("detail", res_json)

    def test_submit_words_not_a_list(self):
        payload = {"words": "cat"}
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(400, response.status_code)
        res_json = json.loads(response.content)
        self.assertIn("detail", res_json)

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
        self.assertIn("detail", res_json)
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
