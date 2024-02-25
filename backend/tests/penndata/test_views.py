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
    def setUp(self):
        call_command("get_calendar")

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
        self.event1 = Event.objects.create(
            event_type="type1",
            name="Event 1",
            description="Description 1",
            start="2024-02-14T10:00:00Z",
            end="2099-02-14T12:00:00Z",
            location="Location 1",
            website="https://pennlabs.org/"
        )
        self.event2 = Event.objects.create(
            event_type="type2",
            name="Event 2",
            description="Description 2",
            start="2024-02-15T10:00:00Z",
            end="2099-02-15T12:00:00Z",
            location="Location 2",
            website="https://pennlabs.org/"
        )

    def test_response(self):
        event1 = Event.objects.get(name="test1")
        event2 = Event.objects.get(name="test2")
        self.assertEqual(event1.name, "test1")
        self.assertEqual(event2.name, "test2")

    def test_get_all_events(self):
        """Test GET request to retrieve all events"""
        url = reverse("events")
        response = self.client.get(url)
        events = Event.objects.all()
        expected_data = [
            {
                "event_type": event.event_type,
                "name": event.name,
                "description": event.description,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "location": event.location,
                "website": event.website,
            }
            for event in events
        ]
        self.assertEqual(response.data, expected_data)

    def test_get_events_by_type(self):
        """Test GET request to retrieve events by type"""
        url = reverse("events-type", kwargs={"type": "type1"})
        response = self.client.get(url)
        events = Event.objects.filter(event_type="type1")
        expected_data = [
            {
                "event_type": event.event_type,
                "name": event.name,
                "description": event.description,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "location": event.location,
                "website": event.website,
            }
            for event in events
        ]
        self.assertEqual(response.data, expected_data)

    def test_get_events_no_type(self):
        """Test GET request to retrieve all events when no type is specified"""
        url = reverse("events")
        response = self.client.get(url)
        events = Event.objects.all()
        expected_data = [
            {
                "event_type": event.event_type,
                "name": event.name,
                "description": event.description,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "location": event.location,
                "website": event.website,
            }
            for event in events
        ]
        self.assertEqual(response.data, expected_data)


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

        self.assertEqual(res_json[2]["type"], "laundry")
        self.assertEqual(res_json[2]["info"]["room_id"], 0)

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

        self.assertEqual(new_res_json[2]["info"]["room_id"], 3)

        self.assertEqual(new_res_json[1]["type"], "news")


class TestGetRecentFitness(TestCase):
    def setUp(self):
        call_command("load_fitness_rooms")
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.client.force_authenticate(user=self.test_user)

        self.fitness_room = FitnessRoom.objects.first()
        self.new_count = 20
        self.new_time = timezone.localtime().replace(second=0, microsecond=0)
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
        for room_obj in res_json:
            room_obj.pop("open")
            room_obj.pop("close")

        expected = [
            {
                "id": room.id,
                "name": room.name,
                "image_url": room.image_url,
                "last_updated": None,
                "count": None,
                "capacity": None,
            }
            for room in FitnessRoom.objects.all()
            if room.id != self.fitness_room.id
        ]
        expected.append(
            {
                "id": self.fitness_room.id,
                "name": self.fitness_room.name,
                # this format: 2023-03-12T16:56:51-04:00
                "last_updated": self.new_time.strftime("%Y-%m-%dT%H:%M:%S%z")[:-2] + ":00",
                "image_url": self.fitness_room.image_url,
                "count": self.new_count,
                "capacity": None,
            }
        )

        # sort both
        expected.sort(key=lambda x: x["id"])
        res_json.sort(key=lambda x: x["id"])

        self.assertEqual(expected, res_json)


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

        # does not create duplicate snapshots
        self.assertEqual(FitnessSnapshot.objects.all().count(), 9)


class TestFitnessUsage(TestCase):
    def load_snapshots_1(self, date):
        # 6:00, 0
        FitnessSnapshot.objects.create(
            room=self.room, date=date + datetime.timedelta(hours=6), count=0, capacity=0.0,
        )
        # 7:30, 10
        FitnessSnapshot.objects.create(
            room=self.room,
            date=date + datetime.timedelta(hours=7, minutes=30),
            count=10,
            capacity=10.0,
        )
        # 8:00, 65
        FitnessSnapshot.objects.create(
            room=self.room, date=date + datetime.timedelta(hours=8), count=65, capacity=65.0,
        )
        # 8:30, 0
        FitnessSnapshot.objects.create(
            room=self.room,
            date=date + datetime.timedelta(hours=8, minutes=30),
            count=0,
            capacity=0.0,
        )
        # 10:00, 60
        FitnessSnapshot.objects.create(
            room=self.room, date=date + datetime.timedelta(hours=10), count=60, capacity=60.0,
        )
        # 20:00, 0
        FitnessSnapshot.objects.create(
            room=self.room,
            date=date + datetime.timedelta(hours=20, minutes=0),
            count=0,
            capacity=0.0,
        )

    def load_snapshots_2(self, date):
        # 7:30, 3
        FitnessSnapshot.objects.create(
            room=self.room,
            date=date + datetime.timedelta(hours=7, minutes=30),
            count=3,
            capacity=3.0,
        )
        # 16:30, 93
        FitnessSnapshot.objects.create(
            room=self.room,
            date=date + datetime.timedelta(hours=16, minutes=30),
            count=93,
            capacity=93.0,
        )

    def setUp(self):
        self.client = APIClient()
        self.date = timezone.make_aware(datetime.datetime(2023, 1, 19, 0, 0, 0))
        self.room = FitnessRoom.objects.create(name="test")

    def test_get_fitness_usage_1(self):
        self.load_snapshots_1(self.date)
        response = self.client.get(
            reverse("fitness-usage", args=[self.room.id]),
            {"date": self.date.strftime("%Y-%m-%d"), "field": "capacity"},
        )
        res_json = json.loads(response.content)

        usage = [
            0,
            0,
            0,
            0,
            0,
            0,
            0.0,
            6.666666666666667,
            65.0,
            20.0,
            60.0,
            54.0,
            48.0,
            42.0,
            36.0,
            30.0,
            24.0,
            18.0,
            12.0,
            6.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]

        expected = {
            "room_name": self.room.name,
            "start_date": self.date.strftime("%Y-%m-%d"),
            "end_date": self.date.strftime("%Y-%m-%d"),
            "usage": {str(i): amt for i, amt in enumerate(usage)},
        }

        self.assertEqual(res_json, expected)

    def test_get_fitness_usage_2(self):
        self.load_snapshots_2(self.date)
        response = self.client.get(
            reverse("fitness-usage", args=[self.room.id]),
            {"date": (self.date).strftime("%Y-%m-%d")},
        )
        res_json = json.loads(response.content)
        usage = [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.0,
            8.0,
            18.0,
            28.0,
            38.0,
            48.0,
            58.0,
            68.0,
            78.0,
            88.0,
            86.35714285714286,
            73.07142857142857,
            59.785714285714285,
            46.5,
            33.214285714285715,
            19.92857142857143,
            6.642857142857139,
        ]

        expected = {
            "room_name": self.room.name,
            "start_date": (self.date).strftime("%Y-%m-%d"),
            "end_date": (self.date).strftime("%Y-%m-%d"),
            "usage": {str(i): amt for i, amt in enumerate(usage)},
        }

        self.assertEqual(res_json, expected)

    def test_get_usage_2_samples_week(self):
        self.load_snapshots_1(self.date)
        self.load_snapshots_2(self.date - datetime.timedelta(days=7))
        response = self.client.get(
            reverse("fitness-usage", args=[self.room.id]),
            {
                "date": (self.date).strftime("%Y-%m-%d"),
                "num_samples": 2,
                "group_by": "week",
                "field": "capacity",
            },
        )
        res_json = json.loads(response.content)
        usage1 = [
            0,
            0,
            0,
            0,
            0,
            0,
            0.0,
            6.666666666666667,
            65.0,
            20.0,
            60.0,
            54.0,
            48.0,
            42.0,
            36.0,
            30.0,
            24.0,
            18.0,
            12.0,
            6.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
        usage2 = [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.0,
            8.0,
            18.0,
            28.0,
            38.0,
            48.0,
            58.0,
            68.0,
            78.0,
            88.0,
            86.35714285714286,
            73.07142857142857,
            59.785714285714285,
            46.5,
            33.214285714285715,
            19.92857142857143,
            6.642857142857139,
        ]
        usage = [(x + y) / 2 for x, y in zip(usage1, usage2)]

        expected = {
            "room_name": self.room.name,
            "start_date": (self.date - datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": (self.date).strftime("%Y-%m-%d"),
            "usage": {str(i): amt for i, amt in enumerate(usage)},
        }

        self.assertEqual(res_json, expected)

    def test_get_usage_2_samples_day(self):
        self.load_snapshots_2(self.date)
        self.load_snapshots_1(self.date - datetime.timedelta(days=1))
        response = self.client.get(
            reverse("fitness-usage", args=[self.room.id]),
            {"date": (self.date).strftime("%Y-%m-%d"), "num_samples": 2},
        )
        res_json = json.loads(response.content)

        usage1 = [
            0,
            0,
            0,
            0,
            0,
            0,
            0.0,
            6.666666666666667,
            65.0,
            20.0,
            60.0,
            54.0,
            48.0,
            42.0,
            36.0,
            30.0,
            24.0,
            18.0,
            12.0,
            6.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
        usage2 = [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.0,
            8.0,
            18.0,
            28.0,
            38.0,
            48.0,
            58.0,
            68.0,
            78.0,
            88.0,
            86.35714285714286,
            73.07142857142857,
            59.785714285714285,
            46.5,
            33.214285714285715,
            19.92857142857143,
            6.642857142857139,
        ]
        usage = [(x + y) / 2 for x, y in zip(usage1, usage2)]

        expected = {
            "room_name": self.room.name,
            "start_date": (self.date - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "end_date": (self.date).strftime("%Y-%m-%d"),
            "usage": {str(i): amt for i, amt in enumerate(usage)},
        }

        self.assertEqual(res_json, expected)

    def test_day_closed(self):
        self.load_snapshots_1(self.date - datetime.timedelta(days=1))
        response = self.client.get(
            reverse("fitness-usage", args=[self.room.id]),
            {"date": (self.date).strftime("%Y-%m-%d")},
        )
        res_json = json.loads(response.content)

        expected = {
            "room_name": self.room.name,
            "start_date": (timezone.localtime()).strftime("%Y-%m-%d"),
            "end_date": (self.date).strftime("%Y-%m-%d"),
            "usage": {str(i): None for i in range(24)},
        }
        self.assertEqual(res_json, expected)

        response = self.client.get(
            reverse("fitness-usage", args=[self.room.id]),
            {"date": (self.date - datetime.timedelta(days=1)).strftime("%Y-%m-%d")},
        )
        res_json = json.loads(response.content)
        usage = [
            0,
            0,
            0,
            0,
            0,
            0,
            0.0,
            6.666666666666667,
            65.0,
            20.0,
            60.0,
            54.0,
            48.0,
            42.0,
            36.0,
            30.0,
            24.0,
            18.0,
            12.0,
            6.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
        expected = {
            "room_name": self.room.name,
            "start_date": (self.date - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "end_date": (self.date - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "usage": {str(i): amt for i, amt in enumerate(usage)},
        }
        self.assertEqual(res_json, expected)

    def test_get_fitness_usage_error(self):
        response = self.client.get(reverse("fitness-usage", args=[self.room.id + 1]))
        self.assertEqual(response.status_code, 404)

        for param in ["date", "num_samples", "group_by", "field"]:
            response = self.client.get(reverse("fitness-usage", args=[self.room.id]), {param: "hi"})
            self.assertEqual(response.status_code, 400)


@mock.patch("requests.get", fakeFitnessGet)
class FitnessPreferencesTestCase(TestCase):
    def setUp(self):
        FitnessRoom.objects.get_or_create(id=0, name="1st Floor Fitness")
        FitnessRoom.objects.get_or_create(id=1, name="MPR")
        FitnessRoom.objects.get_or_create(id=2, name="Pool-Deep")
        FitnessRoom.objects.get_or_create(id=3, name="4th Floor Fitness")
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.fitness_room = FitnessRoom.objects.get(id=0, name="1st Floor Fitness")
        self.other_fitness_room = FitnessRoom.objects.get(id=1, name="MPR")
        self.test_user.profile.fitness_preferences.add(self.fitness_room)

    def test_get(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(reverse("fitness-preferences"))
        res_json = json.loads(response.content)

        self.assertIn(self.fitness_room.id, res_json["rooms"])

    def test_post(self):
        self.client.force_authenticate(user=self.test_user)
        self.client.post(reverse("fitness-preferences"), {"rooms": [self.other_fitness_room.id]})

        response = self.client.get(reverse("fitness-preferences"))
        res_json = json.loads(response.content)

        self.assertIn(self.other_fitness_room.id, res_json["rooms"])


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

    def test_get_unique_counter_no_id(self):
        response = self.client.get(reverse("eventcounter"))
        self.assertEqual(response.status_code, 400)
