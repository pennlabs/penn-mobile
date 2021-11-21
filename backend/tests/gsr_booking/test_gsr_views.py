import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from gsr_booking.models import GSR, GSRBooking


User = get_user_model()


def is_wharton_false(*args):
    return False


def is_wharton_true(*args):
    return True


def libcal_availability(*args):
    with open("tests/gsr_booking/views_libcal_availability.json") as data:
        return json.load(data)


def wharton_availability(*args):
    with open("tests/gsr_booking/views_wharton_availability.json") as data:
        return json.load(data)


def book_cancel_room(*args):
    pass


def reservations(*args):
    with open("tests/gsr_booking/views_reservations.json") as data:
        return json.load(data)


class TestGSRs(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_location(self):
        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)
        for entry in res_json:
            if entry["id"] == 1:
                self.assertEquals(entry["name"], "Huntsman")
            if entry["id"] == 2:
                self.assertEquals(entry["name"], "Academic Research")
            if entry["id"] == 3:
                self.assertEquals(entry["name"], "Weigle")


class TestGSRFunctions(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.user = User.objects.create_user("user", "user@sas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_recent(self):
        gsrs = list(GSR.objects.all())
        GSRBooking.objects.create(user=self.user, room_id=1, room_name="Room 1", gsr=gsrs[0])
        GSRBooking.objects.create(user=self.user, room_id=3, room_name="Room 3", gsr=gsrs[0])
        GSRBooking.objects.create(user=self.user, room_id=2, room_name="Room 2", gsr=gsrs[1])
        GSRBooking.objects.create(user=self.user, room_id=3, room_name="Room 3", gsr=gsrs[2])

        response = self.client.get(reverse("recent-gsrs"))
        res_json = json.loads(response.content)
        self.assertEquals(2, len(res_json))
        self.assertEquals(6, len(res_json[0]))
        self.assertEquals(6, len(res_json[1]))
        self.assertIn("id", res_json[0])
        self.assertIn("kind", res_json[0])
        self.assertIn("lid", res_json[0])
        self.assertIn("gid", res_json[0])
        self.assertIn("name", res_json[0])
        self.assertIn("image_url", res_json[0])
        self.assertNotEqual(res_json[0]["id"], res_json[1]["id"])

    @mock.patch("gsr_booking.views.BW.is_wharton", is_wharton_false)
    def test_get_wharton_false(self):
        response = self.client.get(reverse("is-wharton"))
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertFalse(res_json["is_wharton"])

    @mock.patch("gsr_booking.views.BW.is_wharton", is_wharton_true)
    def test_get_wharton_true(self):
        response = self.client.get(reverse("is-wharton"))
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertTrue(res_json["is_wharton"])

    @mock.patch("gsr_booking.views.BW.get_availability", libcal_availability)
    def test_availability_libcal(self):
        response = self.client.get(reverse("availability", args=["1086", "1889"]))
        res_json = json.loads(response.content)
        self.assertEqual(3, len(res_json))
        self.assertIn("name", res_json)
        self.assertIn("gid", res_json)
        self.assertIn("rooms", res_json)
        if len(res_json["rooms"]) > 0:
            room = res_json["rooms"][0]
            self.assertIn("room_name", room)
            self.assertIn("id", room)
            self.assertIn("availability", room)

    @mock.patch("gsr_booking.views.BW.get_availability", wharton_availability)
    def test_availability_wharton(self):
        response = self.client.get(reverse("availability", args=["JMHH", "1"]))
        res_json = json.loads(response.content)
        self.assertEqual(3, len(res_json))
        self.assertIn("name", res_json)
        self.assertIn("gid", res_json)
        self.assertIn("rooms", res_json)
        if len(res_json["rooms"]) > 0:
            room = res_json["rooms"][0]
            self.assertIn("room_name", room)
            self.assertIn("id", room)
            self.assertIn("availability", room)

    @mock.patch("gsr_booking.views.BW.book_room", book_cancel_room)
    def test_book_libcal(self):
        payload = {
            "start_time": "2021-11-21T18:30:00-05:00",
            "end_time": "2021-11-21T19:00:00-05:00",
            "room_name": "VP WIC Booth 01",
            "id": 7192,
            "gid": 1889,
        }
        response = self.client.post(
            reverse("book"), json.dumps(payload), content_type="application/json"
        )
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("success", res_json["detail"])

    @mock.patch("gsr_booking.views.BW.book_room", book_cancel_room)
    def test_book_wharton(self):
        payload = {
            "start_time": "2021-11-21T18:30:00-05:00",
            "end_time": "2021-11-21T19:00:00-05:00",
            "room_name": "241",
            "id": 94,
            "gid": 1,
        }
        response = self.client.post(
            reverse("book"), json.dumps(payload), content_type="application/json"
        )
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("success", res_json["detail"])

    @mock.patch("gsr_booking.views.BW.cancel_room", book_cancel_room)
    def test_cancel_room(self):
        payload = {"booking_id": "booking id"}
        response = self.client.post(
            reverse("cancel"), json.dumps(payload), content_type="application/json"
        )
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("success", res_json["detail"])

    @mock.patch("gsr_booking.views.BW.get_reservations", reservations)
    def test_reservations(self):
        response = self.client.get(reverse("reservations"))
        res_json = json.loads(response.content)
        self.assertEqual(6, len(res_json))

        entry = res_json[0]

        self.assertIn("booking_id", entry)
        self.assertIn("gsr", entry)
        self.assertIn("room_id", entry)
        self.assertIn("room_name", entry)
        self.assertIn("start", entry)
        self.assertIn("end", entry)

        gsr = entry["gsr"]
        self.assertIn("id", gsr)
        self.assertIn("kind", gsr)
        self.assertIn("lid", gsr)
        self.assertIn("gid", gsr)
        self.assertIn("name", gsr)
        self.assertIn("image_url", gsr)
