import datetime
import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from dining.models import Venue
from laundry.models import LaundryRoom
from penndata.models import Event


User = get_user_model()


class TestNews(TestCase):
    def test_response(self):
        response = self.client.get(reverse("news"))
        res_json = json.loads(response.content)
        self.assertTrue("article" in res_json)
        self.assertEqual(len(res_json), 1)

        article = res_json["article"]
        self.assertEqual(len(article), 5)
        self.assertTrue("link" in article)
        self.assertTrue("title" in article)
        self.assertTrue("subtitle" in article)
        self.assertTrue("timestamp" in article)
        self.assertTrue("imageurl" in article)


class TestCalender(TestCase):
    def test_response(self):
        response = self.client.get(reverse("calendar"))
        res_json = json.loads(response.content)
        self.assertTrue("calendar" in res_json)
        self.assertEqual(len(res_json), 1)

        calendar = res_json["calendar"]
        for event in calendar:
            self.assertEqual(len(event), 3)
            self.assertTrue("start" in event)
            self.assertTrue("end" in event)
            self.assertTrue("name" in event)

            end_date = datetime.datetime.strptime(event["end"], "%Y-%m-%d").date()
            time_diff = (end_date - timezone.localtime().date()).total_seconds()
            self.assertTrue(time_diff <= 1209600)


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
        self.assertTrue(593 in dining_info)
        self.assertTrue(1442 in dining_info)
        self.assertTrue(636 in dining_info)

        self.assertEqual(res_json[3]["type"], "laundry")
        self.assertEqual(res_json[3]["info"]["room_id"], 0)

        self.profile.dining_preferences.add(Venue.objects.get(venue_id=747))
        self.profile.dining_preferences.add(Venue.objects.get(venue_id=1733))
        self.profile.dining_preferences.add(Venue.objects.get(venue_id=638))

        self.profile.laundry_preferences.add(LaundryRoom.objects.get(hall_id=3))
        self.profile.laundry_preferences.add(LaundryRoom.objects.get(hall_id=4))
        self.profile.laundry_preferences.add(LaundryRoom.objects.get(hall_id=5))

        new_response = self.client.get(reverse("homepage"))
        new_res_json = json.loads(new_response.content)["cells"]

        new_dining_info = new_res_json[0]["info"]["venues"]

        self.assertTrue(747 in new_dining_info)
        self.assertTrue(1733 in new_dining_info)
        self.assertTrue(638 in new_dining_info)

        self.assertEqual(new_res_json[3]["info"]["room_id"], 3)

        self.assertEqual(new_res_json[1]["type"], "news")
        self.assertEqual(new_res_json[2]["type"], "calendar")
