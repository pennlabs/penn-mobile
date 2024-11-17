import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from laundry.models import LaundryRoom, LaundrySnapshot
from tests.laundry.test_commands import mock_laundry_get


User = get_user_model()


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class HallIdViewTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            room_id=14089,
            name="English House",
            location="English House",
            location_id=14146,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14099,
            name="Harnwell 10th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14100,
            name="Harnwell 12th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("hall-ids"))
        res_json = json.loads(response.content)
        for hall in res_json:
            self.assertTrue(
                LaundryRoom.objects.filter(
                    name=hall["name"], room_id=hall["hall_id"], location=hall["location"]
                )
            )


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class HallInfoViewTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            room_id=14089,
            name="English House",
            location="English House",
            location_id=14146,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14099,
            name="Harnwell 10th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14100,
            name="Harnwell 12th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        self.laundry_room = LaundryRoom.objects.get(room_id=14089)
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("hall-info", args=[self.laundry_room.room_id]))
        res_json = json.loads(response.content)
        if response.status_code == 200:
            self.assertEqual(self.laundry_room.name, res_json["hall_name"])
            self.assertEqual(self.laundry_room.location, res_json["location"])
        elif response.status_code == 503:
            self.assertEqual("The laundry api is currently unavailable.", res_json["error"])

    def test_hall_error(self):
        response = self.client.get(reverse("hall-info", args=[1000000]))
        self.assertEqual(404, response.status_code)


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class MultipleHallInfoViewTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            room_id=14089,
            name="English House",
            location="English House",
            location_id=14146,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14099,
            name="Harnwell 10th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14100,
            name="Harnwell 12th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        self.laundry_room = LaundryRoom.objects.get(room_id=14089)
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("multiple-hall-info", args=["0,1,2"]))
        res_json = json.loads(response.content)
        if response.status_code == 200:
            rooms = res_json["rooms"]

            for room in rooms:
                self.assertTrue(LaundryRoom.objects.filter(room_id=room["id"]))
                self.assertIn("machines", room)
                self.assertIn("washers", room["machines"])
                self.assertIn("dryers", room["machines"])
                self.assertIn("usage_data", room)
                self.assertIn("hall_name", room["usage_data"])
                self.assertIn("day_of_week", room["usage_data"])
                self.assertIn("washer_data", room["usage_data"])

        elif response.status_code == 503:
            self.assertEqual("The laundry api is currently unavailable.", res_json["error"])

    def test_hall_error(self):
        response = self.client.get(reverse("multiple-hall-info", args=["1000000"]))
        self.assertEqual(404, response.status_code)


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class HallUsageViewTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            room_id=14089,
            name="English House",
            location="English House",
            location_id=14146,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14099,
            name="Harnwell 10th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14100,
            name="Harnwell 12th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        self.laundry_room = LaundryRoom.objects.get(room_id=14089)
        self.snapshot = LaundrySnapshot.objects.create(
            room=self.laundry_room, available_washers=3, available_dryers=3
        )
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("hall-usage", args=[self.laundry_room.room_id]))
        res_json = json.loads(response.content)

        time = timezone.localtime()
        hour = time.hour

        self.assertEqual(self.snapshot.available_washers, res_json["washer_data"][str(hour)])
        self.assertEqual(self.snapshot.available_dryers, res_json["dryer_data"][str(hour)])


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class PreferencesTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            room_id=14089,
            name="English House",
            location="English House",
            location_id=14146,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14099,
            name="Harnwell 10th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        LaundryRoom.objects.get_or_create(
            room_id=14100,
            name="Harnwell 12th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.laundry_room = LaundryRoom.objects.get(room_id=14089)
        self.other_laundry_room = LaundryRoom.objects.get(room_id=14099)
        self.test_user.profile.laundry_preferences.add(self.laundry_room)

    def test_get(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(reverse("preferences"))
        res_json = json.loads(response.content)

        self.assertIn(self.laundry_room.room_id, res_json["rooms"])

    def test_post(self):
        self.client.force_authenticate(user=self.test_user)
        payload = json.dumps({"rooms": [self.other_laundry_room.room_id]})
        self.client.post(reverse("preferences"), payload, content_type="application/json")

        response = self.client.get(reverse("preferences"))
        res_json = json.loads(response.content)

        self.assertIn(self.other_laundry_room.room_id, res_json["rooms"])
