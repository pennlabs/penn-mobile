import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from laundry.models import LaundryRoom, LaundrySnapshot
from user.models import Profile


User = get_user_model()


class HallsViewTestCase(TestCase):
    def setUp(self):
        self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("halls"))
        res_json = json.loads(response.content)
        if response.status_code == 200:
            self.assertTrue(self.laundry_room.name in res_json)
        elif response.status_code == 503:
            self.assertEqual("The laundry api is currently unavailable.", res_json["error"])


class HallInfoViewTestCase(TestCase):
    def setUp(self):
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


class HallUsageViewTestCase(TestCase):
    def setUp(self):
        self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
        self.snapshot = LaundrySnapshot.objects.create(
            hall_id=self.laundry_room.hall_id,
            available_washers=5,
            available_dryers=10,
            total_washers=15,
            total_dryers=20,
        )
        self.client = APIClient()

    def test_response(self):
        response = self.client.get(reverse("hall-usage", args=[self.laundry_room.hall_id]))
        res_json = json.loads(response.content)

        time = timezone.localtime()
        hour = time.hour

        self.assertEqual(self.snapshot.total_washers, res_json["total_number_of_washers"])
        self.assertEqual(self.snapshot.total_dryers, res_json["total_number_of_dryers"])
        self.assertEqual(self.snapshot.available_washers, res_json["washer_data"][str(hour)])
        self.assertEqual(self.snapshot.available_dryers, res_json["dryer_data"][str(hour)])


class PreferencesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
        self.other_laundry_room = LaundryRoom.objects.get(
            hall_id=1, name="Chestnut Butcher", location="Quad"
        )
        self.profile = Profile.objects.create(user=self.test_user)
        self.profile.preferences.add(self.laundry_room)

    def test_get(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(reverse("preferences"))
        res_json = json.loads(response.content)

        self.assertTrue(self.laundry_room.hall_id in res_json["rooms"])

    def test_post(self):
        self.client.force_authenticate(user=self.test_user)
        self.client.post(reverse("preferences"), {"rooms": [self.other_laundry_room.hall_id]})

        response = self.client.get(reverse("preferences"))
        res_json = json.loads(response.content)

        self.assertTrue(self.other_laundry_room.hall_id in res_json["rooms"])
