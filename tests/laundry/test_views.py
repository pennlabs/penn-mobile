import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from laundry.models import LaundryRoom, LaundrySnapshot
from tests.laundry.test_commands import fakeLaundryGet
from user.models import Profile


User = get_user_model()


@mock.patch("requests.get", fakeLaundryGet)
class HallIdViewTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of 1928 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("hall-ids"))
        res_json = json.loads(response.content)
        for hall in res_json:
            self.assertTrue(
                LaundryRoom.objects.filter(
                    name=hall["name"], hall_id=hall["hall_id"], location=hall["location"]
                )
            )


@mock.patch("requests.get", fakeLaundryGet)
class HallInfoViewTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of 1928 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )
        self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("hall-info", args=[self.laundry_room.hall_id]))
        res_json = json.loads(response.content)
        if response.status_code == 200:
            self.assertEqual(self.laundry_room.name, res_json["hall_name"])
            self.assertEqual(self.laundry_room.location, res_json["location"])
        elif response.status_code == 503:
            self.assertEqual("The laundry api is currently unavailable.", res_json["error"])

    def test_hall_error(self):
        response = self.client.get(reverse("hall-info", args=[1000000]))
        self.assertEqual(404, response.status_code)


@mock.patch("requests.get", fakeLaundryGet)
class MultipleHallInfoViewTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of 1928 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )
        self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("multiple-hall-info", args=["0,1,2,3"]))
        res_json = json.loads(response.content)
        if response.status_code == 200:
            rooms = res_json["rooms"]

            for room in rooms:
                self.assertTrue(LaundryRoom.objects.filter(hall_id=room["id"]))
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


@mock.patch("requests.get", fakeLaundryGet)
class HallUsageViewTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of 1928 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )
        self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
        self.snapshot = LaundrySnapshot.objects.create(
            room=self.laundry_room, available_washers=5, available_dryers=10,
        )
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("hall-usage", args=[self.laundry_room.hall_id]))
        res_json = json.loads(response.content)

        time = timezone.localtime()
        hour = time.hour

        self.assertEqual(self.snapshot.available_washers, res_json["washer_data"][str(hour)])
        self.assertEqual(self.snapshot.available_dryers, res_json["dryer_data"][str(hour)])


@mock.patch("requests.get", fakeLaundryGet)
class PreferencesTestCase(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of 1928 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
        self.other_laundry_room = LaundryRoom.objects.get(
            hall_id=1, name="Chestnut Butcher", location="Quad"
        )
        self.profile = Profile.objects.create(user=self.test_user)
        self.profile.laundry_preferences.add(self.laundry_room)

    def test_get(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(reverse("preferences"))
        res_json = json.loads(response.content)

        self.assertIn(self.laundry_room.hall_id, res_json["rooms"])

    def test_post(self):
        self.client.force_authenticate(user=self.test_user)
        self.client.post(reverse("preferences"), {"rooms": [self.other_laundry_room.hall_id]})

        response = self.client.get(reverse("preferences"))
        res_json = json.loads(response.content)

        self.assertIn(self.other_laundry_room.hall_id, res_json["rooms"])
