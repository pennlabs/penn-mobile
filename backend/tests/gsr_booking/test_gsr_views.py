import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from gsr_booking.api_wrapper import APIError
from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking


User = get_user_model()


def create_test_gsrs(cls):
    """Helper to create test GSRs and store references in the class"""
    cls.huntsman_gsr, _ = GSR.objects.get_or_create(
        lid="JMHH",
        gid=1,
        defaults={
            "name": "Huntsman",
            "kind": GSR.KIND_WHARTON,
            "image_url": "https://s3.us-east-2.amazonaws.com/labs.api/gsr/lid-JMHH-gid-1.jpg",
            "in_use": True,
        },
    )
    cls.agh_gsr, _ = GSR.objects.get_or_create(
        lid="20157",
        gid=42437,
        defaults={
            "name": "Amy Gutmann Hall",
            "kind": GSR.KIND_PENNGROUPS,
            "image_url": "https://s3.us-east-2.amazonaws.com/labs.api/gsr/lid-20157-gid-42437.jpg",
            "in_use": True,
        },
    )
    cls.weigle_gsr, _ = GSR.objects.get_or_create(
        lid="1086",
        gid=1889,
        defaults={
            "name": "Weigle",
            "kind": GSR.KIND_LIBCAL,
            "image_url": "https://s3.us-east-2.amazonaws.com/labs.api/gsr/lid-1086-gid-1889.jpg",
            "in_use": True,
        },
    )


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
    @classmethod
    def setUpTestData(cls):
        create_test_gsrs(cls)
        test_user = User.objects.create_user("user1", "user")
        Group.objects.create(owner=test_user, name="Penn Labs", color="blue")

    def setUp(self):
        # Clear cache to avoid stale data from previous tests
        cache.clear()

        # Ensure test GSRs exist (in case setUpTestData didn't run or was reset)
        create_test_gsrs(self.__class__)

        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @mock.patch("gsr_booking.views.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.views.PennGroupsGSRBooker.is_seas", return_value=False)
    def test_get_location(self, mock_is_seas, mock_is_wharton):
        """Test that regular users do not see Wharton or PennGroups GSRs"""
        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)

        gsr_ids = [entry["id"] for entry in res_json]

        # Use class variables
        self.assertNotIn(self.huntsman_gsr.id, gsr_ids)
        self.assertNotIn(self.agh_gsr.id, gsr_ids)
        self.assertIn(self.weigle_gsr.id, gsr_ids)

        self.assertEqual(len(res_json), 1)

    @mock.patch("gsr_booking.views.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.views.PennGroupsGSRBooker.is_seas", return_value=False)
    def test_get_location_regular_user(self, mock_is_seas, mock_is_wharton):
        """Test that regular users only see LibCal GSRs"""
        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)

        # Regular users should only see LibCal GSRs
        # Check kinds from response data directly
        for entry in res_json:
            self.assertIn("kind", entry)
            self.assertEqual(entry["kind"], GSR.KIND_LIBCAL)

    @mock.patch("gsr_booking.views.WhartonGSRBooker.is_wharton", return_value=True)
    @mock.patch("gsr_booking.views.PennGroupsGSRBooker.is_seas", return_value=False)
    def test_get_location_wharton_user(self, mock_is_seas, mock_is_wharton):
        """Test that Wharton users see LibCal and Wharton GSRs"""
        cache.clear()  # Clear cache to ensure fresh data
        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)

        # Wharton users should see LibCal and Wharton GSRs
        kinds_seen = set()
        for entry in res_json:
            self.assertIn("kind", entry)
            kinds_seen.add(entry["kind"])

        self.assertIn(GSR.KIND_LIBCAL, kinds_seen)
        self.assertIn(GSR.KIND_WHARTON, kinds_seen)
        self.assertNotIn(GSR.KIND_PENNGROUPS, kinds_seen)

    @mock.patch("gsr_booking.views.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.views.PennGroupsGSRBooker.is_seas", return_value=True)
    def test_get_location_seas_user(self, mock_is_seas, mock_is_wharton):
        """Test that SEAS users see LibCal and PennGroups GSRs"""
        cache.clear()  # Clear cache to ensure fresh data
        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)

        # SEAS users should see LibCal and PennGroups GSRs
        kinds_seen = set()
        for entry in res_json:
            self.assertIn("kind", entry)
            kinds_seen.add(entry["kind"])

        self.assertIn(GSR.KIND_LIBCAL, kinds_seen)
        self.assertIn(GSR.KIND_PENNGROUPS, kinds_seen)
        self.assertNotIn(GSR.KIND_WHARTON, kinds_seen)

    @mock.patch("gsr_booking.views.WhartonGSRBooker.is_wharton", return_value=True)
    @mock.patch("gsr_booking.views.PennGroupsGSRBooker.is_seas", return_value=True)
    def test_get_location_wharton_seas_user(self, mock_is_seas, mock_is_wharton):
        """Test that users with both Wharton and SEAS access see all non-Penn Labs GSRs"""
        cache.clear()  # Clear cache to ensure fresh data
        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)

        # Users with both should see all kinds
        kinds_seen = set()
        for entry in res_json:
            self.assertIn("kind", entry)
            kinds_seen.add(entry["kind"])

        self.assertIn(GSR.KIND_LIBCAL, kinds_seen)
        self.assertIn(GSR.KIND_WHARTON, kinds_seen)
        self.assertIn(GSR.KIND_PENNGROUPS, kinds_seen)

    def test_get_location_penn_labs_member(self):
        """Test that Penn Labs members see all GSRs regardless of their individual status"""
        # Clear cache before test
        cache.clear()

        # Add user to Penn Labs group
        penn_labs_group = Group.objects.get(name="Penn Labs")
        GroupMembership.objects.create(
            user=self.user, group=penn_labs_group, accepted=True, type=GroupMembership.MEMBER
        )

        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)

        # Penn Labs members should see all GSRs
        # Verify all kinds are present in the response
        kinds_seen = set()
        for entry in res_json:
            self.assertIn("kind", entry)
            kinds_seen.add(entry["kind"])

        # Should see all available kinds (check that all kinds in database are in response)
        expected_kinds = set(GSR.objects.values_list("kind", flat=True).distinct())

        # Verify that all expected kinds are present (use subset check for robustness)
        self.assertTrue(
            expected_kinds.issubset(kinds_seen),
            f"Expected kinds {expected_kinds} not all found in {kinds_seen}",
        )

        # Verify that test GSRs are present
        gsr_ids = [entry["id"] for entry in res_json]
        self.assertIn(self.huntsman_gsr.id, gsr_ids, "Huntsman GSR should be visible")
        self.assertIn(self.agh_gsr.id, gsr_ids, "AGH GSR should be visible")
        self.assertIn(self.weigle_gsr.id, gsr_ids, "Weigle GSR should be visible")

    @mock.patch("gsr_booking.views.WhartonGSRBooker.is_wharton", side_effect=APIError("API Error"))
    @mock.patch("gsr_booking.views.PennGroupsGSRBooker.is_seas", side_effect=APIError("API Error"))
    def test_get_location_api_error_handling(self, mock_is_seas, mock_is_wharton):
        """Test that API errors are handled gracefully and users still see LibCal GSRs"""
        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)

        # Even if API calls fail, users should still see LibCal GSRs
        for entry in res_json:
            self.assertIn("kind", entry)
            self.assertEqual(entry["kind"], GSR.KIND_LIBCAL)


class TestGSRFunctions(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_gsrs(cls)
        test_user = User.objects.create_user("user1", "user")
        Group.objects.create(owner=test_user, name="Penn Labs", color="blue")

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
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
        self.assertEqual(2, len(res_json))
        self.assertEqual(6, len(res_json[0]))
        self.assertEqual(6, len(res_json[1]))
        self.assertIn("id", res_json[0])
        self.assertIn("kind", res_json[0])
        self.assertIn("lid", res_json[0])
        self.assertIn("gid", res_json[0])
        self.assertIn("name", res_json[0])
        self.assertIn("image_url", res_json[0])
        self.assertNotEqual(res_json[0]["id"], res_json[1]["id"])

    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.is_wharton", is_wharton_false)
    def test_get_wharton_false(self):
        response = self.client.get(reverse("is-wharton"))
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertFalse(res_json["is_wharton"])

    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.is_wharton", is_wharton_true)
    def test_get_wharton_true(self):
        response = self.client.get(reverse("is-wharton"))
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertTrue(res_json["is_wharton"])

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.get_availability", libcal_availability)
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

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.get_availability", wharton_availability)
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

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.book_room", book_cancel_room)
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

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.book_room", book_cancel_room)
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

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.cancel_room", book_cancel_room)
    def test_cancel_room(self):
        payload = {"booking_id": "booking id"}
        response = self.client.post(
            reverse("cancel"), json.dumps(payload), content_type="application/json"
        )
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("success", res_json["detail"])

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.get_reservations", reservations)
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


class TestSEASViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_gsrs(cls)
        test_user = User.objects.create_user("user1", "user")
        Group.objects.create(owner=test_user, name="Penn Labs", color="blue")

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.is_seas", return_value=True)
    def test_check_seas_true(self, mock_is_seas):
        response = self.client.get(reverse("is-seas"))
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertTrue(res_json["is_seas"])

    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.is_seas", return_value=False)
    def test_check_seas_false(self, mock_is_seas):
        response = self.client.get(reverse("is-seas"))
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertFalse(res_json["is_seas"])


def penngroups_availability(*args):
    """Mock AGH availability response"""
    return {
        "name": "Amy Gutmann Hall",
        "gid": 42437,
        "rooms": [
            {
                "room_name": "AGH 206",
                "id": 172129,
                "availability": [
                    {
                        "start_time": "2025-10-30T23:30:00-04:00",
                        "end_time": "2025-10-30T23:59:00-04:00",
                    }
                ],
            },
            {
                "room_name": "AGH 334",
                "id": 191384,
                "availability": [
                    {
                        "start_time": "2025-10-30T23:30:00-04:00",
                        "end_time": "2025-10-30T23:59:00-04:00",
                    }
                ],
            },
        ],
    }


def penngroups_book_cancel(*args):
    """Mock AGH book/cancel response"""
    pass


class TestPennGroupsViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_gsrs(cls)
        test_user = User.objects.create_user("user1", "user")
        Group.objects.create(owner=test_user, name="Penn Labs", color="blue")

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.get_availability", penngroups_availability)
    def test_availability_penngroups(self):
        """Test AGH availability endpoint"""
        response = self.client.get(reverse("availability", args=["20157", "42437"]))
        res_json = json.loads(response.content)
        self.assertEqual(3, len(res_json))
        self.assertIn("name", res_json)
        self.assertIn("gid", res_json)
        self.assertIn("rooms", res_json)
        self.assertEqual("Amy Gutmann Hall", res_json["name"])
        if len(res_json["rooms"]) > 0:
            room = res_json["rooms"][0]
            self.assertIn("room_name", room)
            self.assertIn("id", room)
            self.assertIn("availability", room)

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.book_room", penngroups_book_cancel)
    def test_book_penngroups(self):
        """Test AGH booking endpoint"""
        payload = {
            "start_time": "2025-10-30T23:30:00-04:00",
            "end_time": "2025-10-31T00:00:00-04:00",
            "room_name": "AGH 206",
            "id": 172129,
            "gid": 42437,
        }
        response = self.client.post(
            reverse("book"), json.dumps(payload), content_type="application/json"
        )
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("success", res_json["detail"])

    @mock.patch("gsr_booking.api_wrapper.BookingHandler.cancel_room", penngroups_book_cancel)
    def test_cancel_penngroups(self):
        """Test AGH cancel endpoint"""
        payload = {"booking_id": "476df5dc92c1"}
        response = self.client.post(
            reverse("cancel"), json.dumps(payload), content_type="application/json"
        )
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual("success", res_json["detail"])
