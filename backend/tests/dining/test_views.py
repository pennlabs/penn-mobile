import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from dining.api_wrapper import APIError, DiningAPIWrapper
from dining.models import Venue, DiningMenu


User = get_user_model()


def mock_dining_requests(url, *args, **kwargs):
    class Mock:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if "token" in url:
        file_path = "tests/dining/dining_token.json"
    elif "venues" in args[0]:
        file_path = "tests/dining/venues.json"
    elif "menus" in args[0]:
        file_path = "tests/dining/menu.json"
    else:
        raise ValueError

    with open(file_path) as data:
        return Mock(json.load(data), 200)


def mock_request_raise_error(*args, **kwargs):
    raise ConnectionError


def mock_request_post_error(*args, **kwargs):
    class Mock:
        def json(self):
            return {"error": None}

    return Mock()


class TestTokenAndRequest(TestCase):
    def setUp(self):
        self.wrapper = DiningAPIWrapper()

    def test_expired_token(self):
        self.wrapper.expiration += datetime.timedelta(days=1)
        prev_token = self.wrapper.token
        prev_expiration = self.wrapper.expiration

        self.wrapper.update_token()

        # assert that nothing has changed
        self.assertEqual(prev_token, self.wrapper.token)
        self.assertEqual(prev_expiration, self.wrapper.expiration)

    @mock.patch("requests.post", mock_request_post_error)
    def test_update_token_error(self):
        with self.assertRaises(APIError):
            self.wrapper.update_token()

    @mock.patch("requests.post", mock_dining_requests)
    @mock.patch("requests.request", lambda **kwargs: None)
    def test_request_headers_update(self):
        res = self.wrapper.request(headers=dict())
        self.assertIsNone(res)

    @mock.patch("requests.post", mock_dining_requests)
    @mock.patch("requests.request", mock_request_raise_error)
    def test_request_api_error(self):
        with self.assertRaises(APIError):
            self.wrapper.request()


@mock.patch("requests.post", mock_dining_requests)
@mock.patch("requests.request", mock_dining_requests)
class TestVenues(TestCase):
    def setUp(self):
        call_command("load_venues")

    def test_get(self):
        response = self.client.get(reverse("venues"))
        for entry in response.json():
            self.assertIn("name", entry)
            self.assertIn("days", entry)
            self.assertIn("image", entry)
            self.assertIn("id", entry)
            for day in entry["days"]:
                self.assertIn("date", day)
                self.assertIn("dayparts", day)
        self.assertEqual(16, len(response.json()))


class TestMenus(TestCase):
    @mock.patch("requests.post", mock_dining_requests)
    @mock.patch("requests.request", mock_dining_requests)
    def setUp(self):
        Venue.objects.create(
            venue_id=593,
            name="1920 Commons",
            image_url="https://s3.us-east-2.amazonaws.com/labs.api/dining/1920-commons.jpg",
        )
        call_command("load_next_menu")

    def try_structure(self, data):
        for entry in data:
            self.assertIn("venue", entry)
            self.assertIn("date", entry)
            self.assertIn("start_time", entry)
            self.assertIn("end_time", entry)
            self.assertIn("stations", entry)
            self.assertIn("service", entry)
            for station in entry["stations"]:
                self.assertIn("name", station)
                self.assertIn("items", station)
                for item in station["items"]:
                    self.assertIn("item_id", item)
                    self.assertIn("name", item)
                    self.assertIn("description", item)
                    self.assertIn("ingredients", item)

    def test_get_default(self):
        response = self.client.get(reverse("menus"))
        self.try_structure(response.json())

    def test_get_date(self):
        response = self.client.get("/dining/menus/2022-10-04/")
        self.try_structure(response.json())

    @mock.patch("requests.request", mock_dining_requests)
    def test_skip_venue(self):
        Venue.objects.all().delete()
        Venue.objects.create(venue_id=747, name="Skip", image_url="URL")
        wrapper = DiningAPIWrapper()
        wrapper.load_menu()
        self.assertEqual(DiningMenu.objects.count(), 0)


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
