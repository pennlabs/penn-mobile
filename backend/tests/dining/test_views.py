import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from dining.models import Venue


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


@mock.patch("requests.post", mock_dining_requests)
@mock.patch("requests.request", mock_dining_requests)
class TestVenues(TestCase):
    def setUp(self):
        call_command("load_venues")

    def test_get(self):
        response = self.client.get(reverse("venues"))
        for entry in response.json():
            self.assertIn("name", entry)
            self.assertIn("address", entry)
            self.assertIn("days", entry)
            self.assertIn("image", entry)
            self.assertIn("id", entry)
            for day in entry["days"]:
                self.assertIn("date", day)
                self.assertIn("status", day)
                self.assertIn("dayparts", day)
        # Should be 16, however Lauder Retail is closed
        self.assertEqual(15, len(response.json()))


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
