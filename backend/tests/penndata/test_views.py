import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from dining.models import Venue
from laundry.models import LaundryRoom
from penndata.models import Event


def check_wharton(*args):
    return False


User = get_user_model()


class TestNews(TestCase):
    def test_response(self):
        response = self.client.get(reverse("news"))
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 6)
        self.assertIn("link", res_json)
        self.assertIn("title", res_json)
        self.assertIn("subtitle", res_json)
        self.assertIn("timestamp", res_json)
        self.assertIn("imageurl", res_json)


class TestCalender(TestCase):
    def test_response(self):
        response = self.client.get(reverse("calendar"))
        res_json = json.loads(response.content)

        for event in res_json:
            self.assertEqual(len(event), 2)
            self.assertIn("event", event)
            self.assertIn("date", event)


class TestEvent(TestCase):
    def setUp(self):
        self.client = APIClient()
        Event.objects.create(
            event_type="type",
            name="test1",
            description="asdf",
            image_url="https://pennlabs.org/",
            start_time=timezone.localtime(),
            end_time=timezone.localtime(),
            email="a",
            website="https://pennlabs.org/",
            facebook="https://pennlabs.org/",
        )
        Event.objects.create(
            event_type="type",
            name="test2",
            description="asdaf",
            image_url="https://pennlabs.org/",
            start_time=timezone.localtime(),
            end_time=timezone.localtime(),
            email="a",
            website="https://pennlabs.org/",
            facebook="https://pennlabs.org/",
        )

    def test_response(self):

        response = self.client.get(reverse("events", args=["type"]))
        res_json = json.loads(response.content)
        self.assertEquals(2, len(res_json))
        self.assertEquals(res_json[0]["name"], "test1")
        self.assertEquals(res_json[1]["name"], "test2")


class TestHomePage(TestCase):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def setUp(self):
        call_command("load_venues")
        call_command("load_laundry_rooms")
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")

    def test_first_response(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(reverse("homepage"))
        res_json = json.loads(response.content)["cells"]

        self.assertEqual(res_json[0]["type"], "dining")
        dining_info = res_json[0]["info"]["venues"]
        self.assertIn(593, dining_info)
        self.assertIn(1442, dining_info)
        self.assertIn(636, dining_info)

        self.assertEqual(res_json[3]["type"], "laundry")
        self.assertEqual(res_json[3]["info"]["room_id"], 0)

        self.test_user.profile.dining_preferences.add(Venue.objects.get(venue_id=747))
        self.test_user.profile.dining_preferences.add(Venue.objects.get(venue_id=1733))
        self.test_user.profile.dining_preferences.add(Venue.objects.get(venue_id=638))

        self.test_user.profile.laundry_preferences.add(LaundryRoom.objects.get(hall_id=3))
        self.test_user.profile.laundry_preferences.add(LaundryRoom.objects.get(hall_id=4))
        self.test_user.profile.laundry_preferences.add(LaundryRoom.objects.get(hall_id=5))

        new_response = self.client.get(reverse("homepage"))
        new_res_json = json.loads(new_response.content)["cells"]

        new_dining_info = new_res_json[0]["info"]["venues"]

        self.assertIn(747, new_dining_info)
        self.assertIn(1733, new_dining_info)
        self.assertIn(638, new_dining_info)

        self.assertEqual(new_res_json[3]["info"]["room_id"], 3)

        self.assertEqual(new_res_json[1]["type"], "news")
        self.assertEqual(new_res_json[2]["type"], "calendar")

# class TestFitness(TestCase):
#     # def setUp(self):
#     #     call_command("load_fitness_rooms")
#     #     self.client = APIClient()
#     #     self.test_user = User.objects.create_user("user", "user@a.com", "user")
    
#     def test_get_capacities(self):
#         response = self.client.get(reverse("news"))
#         res_json = json.loads(response.content)
#         print(res_json)
#TODO wait for justin to fix