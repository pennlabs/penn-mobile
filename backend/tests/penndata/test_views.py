import datetime
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
from penndata.models import AnalyticsEvent, Event, FitnessRoom, FitnessSnapshot
from portal.models import Poll, Post


def fakeFitnessGet(url, *args, **kwargs):
    if "docs.google.com/spreadsheets/" in url:
        with open("tests/penndata/fitness_snapshot.html", "rb") as f:
            m = mock.MagicMock(content=f.read())
        return m
    else:
        raise NotImplementedError


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


class TestGetRecentFitness(TestCase):
    def setUp(self):
        call_command("load_fitness_rooms")
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.client.force_authenticate(user=self.test_user)

        self.fitness_room = FitnessRoom.objects.first()
        self.new_count = 20
        self.new_time = timezone.localtime()
        old_count = 10
        old_time = self.new_time - datetime.timedelta(days=1)

        # create old snapshot and new snapshot
        FitnessSnapshot.objects.create(
            room=self.fitness_room, date=old_time, count=old_count,
        )
        FitnessSnapshot.objects.create(
            room=self.fitness_room, date=self.new_time, count=self.new_count,
        )

    def test_get_recent(self):
        response = self.client.get(reverse("fitness"))
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual(str(self.fitness_room), res_json[0]["room"]["name"])
        # remove last 6 characters for timezone, %z doesn't have colon
        self.assertEqual(self.new_time.strftime("%Y-%m-%dT%H:%M:%S.%f"), res_json[0]["date"][:-6])
        self.assertEqual(self.new_count, res_json[0]["count"])


@mock.patch("requests.get", fakeFitnessGet)
class TestGetFitnessSnapshot(TestCase):
    def setUp(self):
        call_command("load_fitness_rooms")

    def test_get_fitness_snapshot(self):

        self.assertEqual(FitnessSnapshot.objects.all().count(), 0)

        call_command("get_fitness_snapshot")

        # checks that all fitness snapshots have been accounted for
        self.assertEqual(FitnessSnapshot.objects.all().count(), 9)

        # asserts that fields are correct, and that all snapshots
        # have been accounted for
        for snapshot in FitnessSnapshot.objects.all():
            self.assertTrue(snapshot.count >= 0)

        call_command("get_fitness_snapshot")

        self.assertEqual(FitnessSnapshot.objects.all().count(), 18)


class TestAnalytics(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.client.force_authenticate(user=self.test_user)

    def test_create_regular_analytics(self):
        payload = {
            "cell_type": "dining",
            "index": 0,
            "is_interaction": False,
            "poll": "",
            "post": "",
        }
        response = self.client.post(reverse("analytics"), payload)
        res_json = response.json()
        self.assertEqual("dining", res_json["cell_type"])
        self.assertIsNone(res_json["post"])
        self.assertIsNone(res_json["poll"])

    def test_create_poll_analytics(self):
        poll = Poll.objects.create(
            club_code="pennlabs",
            question="hello?",
            expire_date=timezone.now() + datetime.timedelta(days=3),
        )
        payload = {
            "cell_type": "poll",
            "index": 10,
            "is_interaction": True,
            "poll": poll.id,
            "post": "",
        }
        response = self.client.post(reverse("analytics"), payload)
        res_json = response.json()
        self.assertEqual("poll", res_json["cell_type"])
        self.assertEqual(10, res_json["index"])
        self.assertIsNotNone(res_json["poll"])
        self.assertIsNone(res_json["post"])
        self.assertTrue(res_json["is_interaction"])

    def test_create_post_analytics(self):
        post = Post.objects.create(
            club_code="notpennlabs",
            title="Test title 2",
            subtitle="Test subtitle 2",
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
        )
        payload = {
            "cell_type": "post",
            "index": 5,
            "is_interaction": False,
            "poll": "",
            "post": post.id,
        }
        response = self.client.post(reverse("analytics"), payload)
        res_json = response.json()
        self.assertEqual("post", res_json["cell_type"])
        self.assertEqual(5, res_json["index"])
        self.assertIsNone(res_json["poll"])
        self.assertIsNotNone(res_json["post"])
        self.assertFalse(res_json["is_interaction"])

    def test_fail_post_poll_analytics(self):
        poll = Poll.objects.create(
            club_code="pennlabs",
            question="hello?",
            expire_date=timezone.now() + datetime.timedelta(days=3),
        )
        post = Post.objects.create(
            club_code="notpennlabs",
            title="Test title 2",
            subtitle="Test subtitle 2",
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
        )
        payload = {
            "cell_type": "dining",
            "index": 0,
            "is_interaction": False,
            "poll": poll.id,
            "post": post.id,
        }
        response = self.client.post(reverse("analytics"), payload)
        res_json = response.json()
        self.assertEqual(400, response.status_code)
        self.assertEqual("Poll and Post interactions are mutually exclusive.", res_json["detail"])


class TestUniqueCounterView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.client.force_authenticate(user=self.test_user)

    def test_get_unique_counter(self):
        post = Post.objects.create(
            club_code="pennlabs",
            title="Test title",
            subtitle="Test subtitle",
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
        )

        AnalyticsEvent.objects.create(
            user=self.test_user,
            cell_type="dining",
            index=0,
            is_interaction=False,
            poll=None,
            post=post,
        )
        response = self.client.get(reverse("eventcounter"), {"post_id": post.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

        response = self.client.get(reverse("eventcounter"), {"poll_id": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)

        response = self.client.get(
            reverse("eventcounter"), {"post_id": post.id, "is_interaction": True}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
