from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from games.models import Game, GameUser, LeaderboardEntry


User = get_user_model()

DATE = "2024-03-15"
BOARD = [["a", "b", "c", "d"], ["e", "f", "g", "h"]]
POSSIBLE_WORDS = ["cat", "dog", "fog", "log", "lag"]
SEED = "abc123"


class TestGameUserProfileView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.user)

    def test_get_profile_defaults_to_anonymized_without_syncing(self):
        with patch("games.models.platform_student_attrs") as sync:
            response = self.client.get("/games/word-hunt/profile/")

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["anonymized"])
        self.assertTrue(GameUser.objects.filter(user=self.user).exists())
        sync.assert_not_called()

    @patch(
        "games.models.platform_student_attrs",
        return_value={"school": "SEAS", "major": "CIS", "graduation_year": 2026},
    )
    def test_patch_profile_updates_anonymization_and_syncs(self, sync):
        response = self.client.patch(
            "/games/word-hunt/profile/", {"anonymized": False}, format="json"
        )

        self.assertEqual(200, response.status_code)
        self.assertFalse(response.json()["anonymized"])
        self.assertEqual("SEAS", response.json()["school"])
        sync.assert_called_once_with(self.user)

    def test_patch_profile_rejects_invalid_anonymized_value(self):
        response = self.client.patch(
            "/games/word-hunt/profile/", {"anonymized": "maybe"}, format="json"
        )

        self.assertEqual(400, response.status_code)
        self.assertIn("anonymized", response.json())


class TestLeaderboardByDateView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        self.user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        self.user3 = User.objects.create_user("user3", "user3@seas.upenn.edu", "user3")
        self.client.force_authenticate(user=self.user1)
        self.game = Game.objects.create(
            date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED
        )

    def create_entry(
        self,
        user,
        score,
        *,
        anonymized=True,
        num_words_found=3,
        school="",
        major="",
        graduation_year=None,
    ):
        game_user = GameUser.for_user(user, anonymized=anonymized)
        game_user.school = school
        game_user.major = major
        game_user.graduation_year = graduation_year
        game_user.save(update_fields=["school", "major", "graduation_year"])
        return LeaderboardEntry.objects.create(
            game=self.game, user=user, score=score, num_words_found=num_words_found
        )

    def leaderboard(self, query=""):
        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/{query}")
        self.assertEqual(200, response.status_code)
        return response.json()

    def test_anonymous_player_is_excluded_but_gets_global_rank(self):
        self.create_entry(self.user1, 300)
        self.create_entry(self.user2, 100, anonymized=False)
        self.create_entry(self.user3, 900)

        response = self.leaderboard()

        self.assertEqual([100], [entry["score"] for entry in response["leaderboard"]])
        self.assertEqual(
            {"score": 300, "rank": 2},
            {"score": response["me"]["score"], "rank": response["me"]["rank"]},
        )
        self.assertIsNone(response["me"]["name"])

    def test_opted_in_name_is_visible_to_anonymous_viewer(self):
        self.user2.first_name, self.user2.last_name = "Ada", "Lovelace"
        self.user2.save()
        self.create_entry(self.user2, 500, anonymized=False)

        self.assertEqual("Ada Lovelace", self.leaderboard()["leaderboard"][0]["name"])

    def test_limit_does_not_change_private_rank(self):
        self.create_entry(self.user1, 300)
        self.create_entry(self.user2, 500, anonymized=False)
        self.create_entry(self.user3, 400, anonymized=False)

        response = self.leaderboard("?limit=1")

        self.assertEqual([500], [entry["score"] for entry in response["leaderboard"]])
        self.assertEqual(3, response["me"]["rank"])

    def test_opted_in_private_rank_includes_anonymous_scores(self):
        GameUser.for_user(self.user1, anonymized=False)
        self.create_entry(self.user1, 300, anonymized=False)
        self.create_entry(self.user2, 500)
        self.create_entry(self.user3, 100, anonymized=False)

        self.assertEqual(2, self.leaderboard()["me"]["rank"])

    def test_tiebreaker_orders_equal_scores_and_preserves_tied_rank(self):
        self.create_entry(self.user1, 300, anonymized=False)
        self.create_entry(self.user2, 300, anonymized=False)

        response = self.leaderboard()

        self.assertLess(
            response["leaderboard"][0]["submitted_at"],
            response["leaderboard"][1]["submitted_at"],
        )
        self.assertEqual([1, 1], [entry["rank"] for entry in response["leaderboard"]])

    def test_sort_by_num_words_found(self):
        self.create_entry(self.user1, 300, anonymized=False, num_words_found=2)
        self.create_entry(self.user2, 200, anonymized=False, num_words_found=5)

        response = self.leaderboard("?sort=-num_words_found")

        self.assertEqual([5, 2], [entry["num_words_found"] for entry in response["leaderboard"]])

    def test_filters_apply_to_public_results_and_private_rank(self):
        self.create_entry(self.user1, 300, school="SEAS", major="CIS", graduation_year=2026)
        self.create_entry(
            self.user2,
            500,
            anonymized=False,
            school="Wharton",
            major="FIN",
            graduation_year=2027,
        )
        self.create_entry(
            self.user3,
            400,
            anonymized=False,
            school="SEAS",
            major="CIS",
            graduation_year=2026,
        )

        for query in ("?school=SEAS", "?major=CIS", "?year=2026"):
            response = self.leaderboard(query)
            self.assertEqual([400], [entry["score"] for entry in response["leaderboard"]])
            self.assertEqual(2, response["me"]["rank"])

    def test_invalid_leaderboard_parameters_are_rejected(self):
        for query in ("?sort=password", "?limit=-1", "?year=abc"):
            response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/{query}")
            self.assertEqual(400, response.status_code)

    def test_leaderboard_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(f"/games/word-hunt/{DATE}/leaderboard/")

        self.assertEqual(403, response.status_code)


class TestSubmitScoreView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        self.client.force_authenticate(user=self.user)
        Game.objects.create(date=DATE, board=BOARD, possible_words=POSSIBLE_WORDS, seed=SEED)

    @patch("games.models.platform_student_attrs")
    def test_valid_submission_does_not_update_profile_or_sync(self, sync):
        response = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", {"words": ["cat"]}, format="json"
        )

        self.assertEqual(201, response.status_code)
        self.assertEqual(100, response.json()["score"])
        self.assertIsNone(response.json()["rank"])
        self.assertFalse(GameUser.objects.filter(user=self.user).exists())
        sync.assert_not_called()

    def test_invalid_and_duplicate_submissions_are_rejected(self):
        invalid = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", {"words": ["unknown"]}, format="json"
        )
        valid = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", {"words": ["cat"]}, format="json"
        )
        duplicate = self.client.post(
            f"/games/word-hunt/{DATE}/submit/", {"words": ["cat"]}, format="json"
        )

        self.assertEqual(400, invalid.status_code)
        self.assertEqual(201, valid.status_code)
        self.assertEqual(400, duplicate.status_code)
