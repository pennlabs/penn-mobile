import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from dining.models import DiningBalance, DiningTransaction, Venue


User = get_user_model()


def mock_requests_get(url, *args, **kwargs):
    class Mock:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if "venues" in url:
        file_path = "tests/dining/venue.json"
    elif "cafes&cafe=" in url:
        file_path = "tests/dining/hours.json"
    elif "menus&cafe=" in url:
        file_path = "tests/dining/menu.json"
    else:
        file_path = "tests/dining/item.json"

    with open(file_path) as data:
        return Mock(json.load(data), 200)


@mock.patch("requests.get", mock_requests_get)
class TestVenues(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

    def test_get(self):

        response = self.client.get(reverse("venues"))
        res_json = json.loads(response.content)
        venues = res_json["document"]["venue"]
        self.assertTrue(len(venues[0]) > 0)


@mock.patch("requests.get", mock_requests_get)
class TestHours(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

    def test_get(self):
        response = self.client.get(reverse("hours", args=["593"]))
        commons = json.loads(response.content)["cafes"]["593"]
        self.assertEquals("1920 Commons", commons["name"])
        self.assertTrue(len(commons["days"]) > 2)


@mock.patch("requests.get", mock_requests_get)
class TestMenu(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

    def test_weekly_get(self):
        response = self.client.get(reverse("weekly-menu", args=["593"]))
        commons = json.loads(response.content)["Document"]["tblMenu"][0]
        self.assertEquals(commons["menudate"], timezone.localtime().date().strftime("%-m/%d/%Y"))

    def test_daily_get(self):
        response = self.client.get(reverse("daily-menu", args=["593"]))
        commons = json.loads(response.content)["Document"]
        self.assertEquals(commons["menudate"], timezone.localtime().date().strftime("%-m/%d/%Y"))


@mock.patch("requests.get", mock_requests_get)
class TestItem(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

    def test_get(self):

        response = self.client.get(reverse("item-info", args=["123"]))
        french_toast = json.loads(response.content)["items"]["123"]
        self.assertEquals(french_toast["label"], "Texas French Toast")


class TestPreferences(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

        self.test_user = User.objects.create_user("user", "user@a.com", "user")

        preference = self.test_user.profile.dining_preferences
        preference.add(Venue.objects.get(venue_id=593))
        preference.add(Venue.objects.get(venue_id=593))
        preference.add(Venue.objects.get(venue_id=593))
        preference.add(Venue.objects.get(venue_id=636))
        preference.add(Venue.objects.get(venue_id=636))
        preference.add(Venue.objects.get(venue_id=637))

    def test_get(self):
        self.client.force_authenticate(user=self.test_user)

        response = self.client.get(reverse("dining-preferences"))
        res_json = json.loads(response.content)["preferences"]

        for item in res_json:
            if item["venue_id"] == 593:
                self.assertEqual(item["count"], 1)
            elif item["venue_id"] == 636:
                self.assertEqual(item["count"], 1)
            else:
                self.assertEqual(item["count"], 1)

    def test_post(self):
        self.client.force_authenticate(user=self.test_user)
        self.client.post(
            reverse("dining-preferences"),
            json.dumps({"venues": ["641", "641", "641", "1733"]}),
            content_type="application/json",
        )

        preference = self.test_user.profile.dining_preferences

        self.assertEqual(preference.count(), 2)

        self.assertIn(Venue.objects.get(venue_id=641), preference.all())
        self.assertIn(Venue.objects.get(venue_id=1733), preference.all())


class TestTransactions(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

        self.test_user = User.objects.create_user("user", "user@a.com", "user")

        DiningTransaction.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            description="test1",
            amount=321,
            balance=123,
        )
        DiningTransaction.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            description="test2",
            amount=3211,
            balance=1223,
        )
        DiningTransaction.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            description="test3",
            amount=321,
            balance=123,
        )

    def test_get(self):
        self.client.force_authenticate(user=self.test_user)

        response = self.client.get(reverse("dining-transactions"))
        res_json = json.loads(response.content)

        self.assertEqual(len(res_json), 3)
        self.assertEqual(res_json[0]["description"], "test1")

    def test_post(self):
        pass


class TestBalance(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

        self.test_user = User.objects.create_user("user", "user@a.com", "user")

        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            dining_dollars=1,
            swipes=1,
            guest_swipes=1,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            dining_dollars=2,
            swipes=2,
            guest_swipes=2,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            dining_dollars=3,
            swipes=3,
            guest_swipes=3,
        )

    def test_get(self):
        self.client.force_authenticate(user=self.test_user)

        response = self.client.get(reverse("dining-balance"))
        res_json = json.loads(response.content)["balance"]

        self.assertEqual(res_json["dining_dollars"], 3)
        self.assertEqual(res_json["swipes"], 3)
        self.assertEqual(res_json["guest_swipes"], 3)

    def test_post(self):
        pass


class TestAverageBalance(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

        self.test_user = User.objects.create_user("user", "user@a.com", "user")

        self.date = timezone.localtime().strftime("%Y-%m-%d")

        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            dining_dollars=2,
            swipes=1,
            guest_swipes=1,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            dining_dollars=4,
            swipes=2,
            guest_swipes=2,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime(),
            dining_dollars=6,
            swipes=3,
            guest_swipes=3,
        )

    def test_get(self):

        self.client.force_authenticate(user=self.test_user)

        url = "/dining/balances?start_date={}&end_date={}".format(self.date, self.date)

        response = self.client.get(url, headers={"X-Account-ID": "12345"})
        res_json = json.loads(response.content)["balance"][0]
        self.assertEqual(res_json["dining_dollars"], 4)
        self.assertEqual(res_json["swipes"], 2)
        self.assertEqual(res_json["guest_swipes"], 2)


class TestProjection(TestCase):
    def setUp(self):
        call_command("load_venues")
        self.client = APIClient()

        self.test_user = User.objects.create_user("user", "user@a.com", "user")

        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime() - datetime.timedelta(days=1),
            dining_dollars=1,
            swipes=1,
            guest_swipes=1,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime() - datetime.timedelta(days=2),
            dining_dollars=2,
            swipes=2,
            guest_swipes=2,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime() - datetime.timedelta(days=3),
            dining_dollars=3,
            swipes=3,
            guest_swipes=3,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime() - datetime.timedelta(days=4),
            dining_dollars=4,
            swipes=4,
            guest_swipes=4,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime() - datetime.timedelta(days=5),
            dining_dollars=5,
            swipes=5,
            guest_swipes=5,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime() - datetime.timedelta(days=6),
            dining_dollars=6,
            swipes=6,
            guest_swipes=6,
        )
        DiningBalance.objects.create(
            profile=self.test_user.profile,
            date=timezone.localtime() - datetime.timedelta(days=7),
            dining_dollars=7,
            swipes=7,
            guest_swipes=7,
        )

    def test_get(self):

        self.client.force_authenticate(user=self.test_user)

        response = self.client.get(reverse("dining-projection"))
        res_json = json.loads(response.content)["projection"]

        self.assertTrue(isinstance(res_json["swipes_day_left"], float))
        self.assertTrue(isinstance(res_json["dining_dollars_day_left"], float))
        self.assertTrue(isinstance(res_json["swipes_left_on_date"], float))
        self.assertTrue(isinstance(res_json["dollars_left_on_date"], float))
