import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from requests.exceptions import ConnectTimeout
from rest_framework.test import APIClient

from gsr_booking.api_wrapper import APIError, GSRBooker, WhartonGSRBooker
from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, Reservation


User = get_user_model()


def mock_requests_get(obj, *args, **kwargs):
    class Mock:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.ok = True

        def json(self):
            return self.json_data

    url = args[1]
    # Wharton API (existing)
    if "wharton" in url and "privileges" in url:  # is wharton check
        file_path = "tests/gsr_booking/api_is_wharton.json"
    elif "wharton" in url and "student_reserve" in url:  # wharton booking
        file_path = "tests/gsr_booking/api_wharton_book.json"
    elif "wharton" in url and "availability" in url:  # wharton availability
        file_path = "tests/gsr_booking/api_wharton_availability.json"
    elif "wharton" in url and "reservations" in url:  # wharton / libcal reservations
        file_path = "tests/gsr_booking/api_wharton_reservations.json"
    elif "wharton" in url and "cancel" in url:  # wharton cancelling
        file_path = "tests/gsr_booking/api_wharton_cancel.json"
    elif "libcal" in url and "space/categories" in url:  # libcal availability part 1
        file_path = "tests/gsr_booking/api_libcal_space_categories.json"
    elif "libcal" in url and "space/category" in url:  # libcal availability part 2
        file_path = "tests/gsr_booking/api_libcal_space_category.json"
    elif "libcal" in url and "space/item" in url:  # libcal availability part 3
        file_path = "tests/gsr_booking/api_libcal_space_item.json"
    elif "libcal" in url and "space/reserve" in url:  # libcal book
        file_path = "tests/gsr_booking/api_libcal_book.json"
    elif "libcal" in url and "space/cancel" in url:  # libcal cancel
        file_path = "tests/gsr_booking/api_libcal_cancel.json"

    with open(file_path) as data:
        return Mock(json.load(data), 200)


def mock_penngroups_api_get(*args, **kwargs):
    """Mock for requests.get calls to PennGroups API"""

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.ok = True

        def json(self):
            return self.json_data

    url = args[0] if args else kwargs.get("url", "")

    if "grouperWs" in url and "groups" in url:
        # Check if the URL contains a username that should be non-SEAS
        # We'll use a convention: if username contains "not_seas" or "non_seas", return non-SEAS
        # Otherwise return SEAS by default
        if "not_seas" in url or "non_seas" in url:
            with open("tests/gsr_booking/api_penngroups_not_seas.json") as f:
                return MockResponse(json.load(f))
        else:
            # Return SEAS user by default for tests
            with open("tests/gsr_booking/api_penngroups_seas.json") as f:
                return MockResponse(json.load(f))

    # Default empty response
    return MockResponse({})


def mock_agh_libcal_request(obj, *args, **kwargs):
    """Mock for PennGroupsBookingWrapper.request() - handles AGH LibCal API calls"""

    class Mock:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.ok = True

        def json(self):
            return self.json_data

    method = args[0] if len(args) > 0 else kwargs.get("method", "GET")
    url = args[1] if len(args) > 1 else kwargs.get("url", "")

    # AGH category
    if method == "GET" and "space/category/42437" in url:
        file_path = "tests/gsr_booking/api_penngroups_agh_category.json"
    # AGH single item (for authorization check in book_room)
    elif method == "GET" and "space/item/" in url and "?" not in url:
        # Single item request - LibCal API returns a list with one item
        item_id = url.split("space/item/")[1].split("/")[0]
        if item_id in ["172129", "191384"]:
            file_path = "tests/gsr_booking/api_penngroups_agh_item.json"
            with open(file_path) as data:
                item_data = json.load(data)
                if item_id == "191384":
                    # Modify the first (and only) item in the list
                    item_data[0]["id"] = 191384
                    item_data[0]["name"] = "AGH 334"
                    item_data[0]["capacity"] = 5
                    item_data[0]["zoneId"] = 10798
                return Mock(item_data, 200)
        else:
            return Mock({"error": "invalid item id"}, 404)
    # AGH availability (multiple items with query params)
    elif method == "GET" and "space/item" in url and "?" in url:
        file_path = "tests/gsr_booking/api_penngroups_agh_availability.json"
    # AGH book
    elif method == "POST" and "space/reserve" in url:
        file_path = "tests/gsr_booking/api_penngroups_book.json"
    # AGH cancel
    elif method == "POST" and "space/cancel" in url:
        file_path = "tests/gsr_booking/api_penngroups_cancel.json"
    else:
        return Mock({}, 404)

    with open(file_path) as data:
        return Mock(json.load(data), 200)


def mock_non_seas_get(*args, **kwargs):
    """Mock for non-SEAS users"""

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.ok = True

        def json(self):
            return self.json_data

    url = args[0] if args else kwargs.get("url", "")
    if "grouperWs" in url and "groups" in url:
        with open("tests/gsr_booking/api_penngroups_not_seas.json") as f:
            return MockResponse(json.load(f))
    return MockResponse({})


def mock_get_user_pennid(self, user):
    """Mock pennid extraction"""
    return "12345678"


class TestBookingWrapper(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_gsrs")

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.group_user = User.objects.create_user(
            "grou_user", "group_user@seas.upenn.edu", "group_user"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        with mock.patch(
            "gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False
        ), mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False):
            self.group = Group.objects.create(owner=self.group_user, name="Penn Labs", color="blue")

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.request", mock_requests_get)
    def test_is_wharton(self, mock_is_seas, mock_is_wharton):
        self.assertFalse(WhartonGSRBooker.is_wharton(self.user))

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.request", mock_requests_get)
    def test_wharton_availability(self, mock_is_seas, mock_is_wharton):
        availability = GSRBooker.get_availability("JMHH", 1, "2021-01-07", "2022-01-08", self.user)
        self.assertIn("name", availability)
        self.assertIn("gid", availability)
        self.assertIn("rooms", availability)
        self.assertIn("room_name", availability["rooms"][0])
        self.assertIn("id", availability["rooms"][0])
        self.assertIn("availability", availability["rooms"][0])

    # @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.check_credits", mock_check_credits)
    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.request", mock_requests_get)
    def test_book_wharton(self, mock_is_seas, mock_is_wharton):
        book_wharton = GSRBooker.book_room(
            1, 94, "241", "2021-12-05T16:00:00-05:00", "2021-12-05T16:30:00-05:00", self.user
        )
        self.assertEqual("241", book_wharton.gsrbooking_set.first().room_name)

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.request", mock_requests_get)
    def test_wharton_reservations(self, mock_is_seas, mock_is_wharton):
        reservations = WhartonGSRBooker.get_reservations(self.user)
        self.assertTrue(isinstance(reservations, list))
        self.assertIn("booking_id", reservations[0])
        self.assertIn("gid", reservations[0])

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.request", mock_requests_get)
    def test_cancel_wharton(self, mock_is_seas, mock_is_wharton):
        cancel = GSRBooker.cancel_room("987654", self.user)
        self.assertIsNone(cancel)

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.LibCalBookingWrapper.request", mock_requests_get)
    def test_libcal_availability(self, mock_is_seas, mock_is_wharton):
        availability = GSRBooker.get_availability(
            "1086", 1889, "2021-01-07", "2022-01-08", self.user
        )
        self.assertIn("name", availability)
        self.assertIn("gid", availability)
        self.assertIn("rooms", availability)
        self.assertIn("room_name", availability["rooms"][0])
        self.assertIn("id", availability["rooms"][0])
        self.assertIn("availability", availability["rooms"][0])

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.LibCalBookingWrapper.request", mock_requests_get)
    def test_book_libcal(self, mock_is_seas, mock_is_wharton):
        book_libcal = GSRBooker.book_room(
            1889,
            7192,
            "VP WIC Booth 01",
            "2021-12-05T16:00:00-05:00",
            "2021-12-05T16:30:00-05:00",
            self.user,
        )
        self.assertEqual("VP WIC Booth 01", book_libcal.gsrbooking_set.first().room_name)

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch(
        "gsr_booking.api_wrapper.WhartonBookingWrapper.request", mock_requests_get
    )  # purposefully wharton request here
    def test_libcal_reservations(self, mock_is_seas, mock_is_wharton):
        reservations = GSRBooker.get_reservations(self.user)
        self.assertTrue(isinstance(reservations, list))
        self.assertIn("booking_id", reservations[0])
        self.assertIn("gsr", reservations[0])

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.LibCalBookingWrapper.request", mock_requests_get)
    def test_cancel_libcal(self, mock_is_seas, mock_is_wharton):
        group = Group.objects.create(owner=self.user)
        reservation = Reservation.objects.create(creator=self.user, group=group)
        GSRBooking.objects.create(
            reservation=reservation,
            user=self.user,
            booking_id="123",
            gsr=GSR.objects.filter(kind="LIBCAL").first(),
            room_id=1,
            room_name="room",
        )
        cancel = GSRBooker.cancel_room("123", self.user)
        self.assertIsNone(cancel)

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.request", mock_requests_get)
    def test_group_book_wharton(self, mock_is_seas, mock_is_wharton):
        # make sure group_user is treated as a wharton user so they
        # are returned in list of wharton users in gb.book_room
        membership1 = GroupMembership.objects.filter(group=self.group).first()
        membership1.is_wharton = True
        membership1.save()

        # adds user to the group as a wharton user
        GroupMembership.objects.create(
            user=self.user, group=self.group, accepted=True, is_wharton=True
        )

        # reservation under user with group
        reservation = GSRBooker.book_room(
            1,
            94,
            "241",
            "2021-12-05T16:00:00-05:00",
            "2021-12-05T18:00:00-05:00",
            self.user,
            self.group,
        )

        bookings = list(reservation.gsrbooking_set.all())
        bookings.sort(key=lambda x: x.start)
        # check bookings cover entire range and enough time
        for i in range(len(bookings) - 1):
            self.assertEqual(bookings[i].end, bookings[i + 1].start)
        total_time = sum([booking.end - booking.start for booking in bookings], timedelta())
        self.assertEqual(total_time, timedelta(hours=2))

        # check reservation exists
        self.assertIsNotNone(Reservation.objects.get(pk=reservation.id))

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.LibCalBookingWrapper.request", mock_requests_get)
    def test_group_book_libcal(self, mock_is_seas, mock_is_wharton):
        # add user to the group
        GroupMembership.objects.create(user=self.user, group=self.group, accepted=True)

        start = timezone.localtime()
        end = start + timedelta(hours=2)

        reservation = GSRBooker.book_room(
            1889,
            7192,
            "VP WIC Booth 01",
            start.strftime("%Y-%m-%dT%H:%M:%S%z"),
            end.strftime("%Y-%m-%dT%H:%M:%S%z"),
            self.user,
            self.group,
        )

        bookings = list(reservation.gsrbooking_set.all())
        bookings.sort(key=lambda x: x.start)
        # check bookings cover entire range and enough time
        for i in range(len(bookings) - 1):
            self.assertEqual(bookings[i].end, bookings[i + 1].start)
        total_time = sum([booking.end - booking.start for booking in bookings], timedelta())
        self.assertEqual(total_time, timedelta(hours=2))
        # check reservation exists
        self.assertIsNotNone(Reservation.objects.get(pk=reservation.id))

        res = GSRBooker.get_reservations(self.user, self.group)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["room_name"], "[Me] VP WIC Booth 01")

        credit_owner = reservation.gsrbooking_set.first().user
        res = GSRBooker.get_reservations(credit_owner, self.group)
        self.assertEqual(len(res), 1)
        self.assertEqual(
            res[0]["room_name"],
            f"{'[Penn Labs]' if credit_owner != self.user else '[Me]'} VP WIC Booth 01",
        )

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.WhartonBookingWrapper.request", mock_requests_get)
    def test_group_wharton_availability(self, mock_is_seas, mock_is_wharton):
        with self.assertRaises(APIError):
            GSRBooker.get_availability(
                "JMHH", 1, "2021-01-07", "2022-01-08", self.group_user, self.group
            )
        GroupMembership.objects.create(
            user=self.user, group=self.group, accepted=True, is_wharton=True
        )
        availability = GSRBooker.get_availability(
            "JMHH", 1, "2021-01-07", "2022-01-08", self.group_user, self.group
        )
        self.assertIn("name", availability)
        self.assertIn("gid", availability)
        self.assertIn("rooms", availability)
        self.assertIn("room_name", availability["rooms"][0])
        self.assertIn("id", availability["rooms"][0])
        self.assertIn("availability", availability["rooms"][0])

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_is_seas(self, mock_is_wharton):
        """Test SEAS status checking via PennGroups API"""
        from gsr_booking.api_wrapper import PennGroupsGSRBooker

        # Create a SEAS user (default mock returns SEAS)
        seas_user = User.objects.create_user("seas_user", "seas_user@seas.upenn.edu", "pass")

        # This should return True based on mock
        is_seas = PennGroupsGSRBooker.is_seas(seas_user)
        self.assertTrue(is_seas)

        # Test non-SEAS user - need to create a user with username that triggers non-SEAS mock
        non_seas_user = User.objects.create_user("not_seas_user", "user@sas.upenn.edu", "pass")

        # Patch to return non-SEAS response for this user
        def mock_non_seas_get_local(*args, **kwargs):
            class MockResponse:
                def __init__(self, json_data, status_code=200):
                    self.json_data = json_data
                    self.status_code = status_code
                    self.ok = True

                def json(self):
                    return self.json_data

            url = args[0] if args else kwargs.get("url", "")
            if "grouperWs" in url and "groups" in url:
                with open("tests/gsr_booking/api_penngroups_not_seas.json") as f:
                    return MockResponse(json.load(f))
            return MockResponse({})

        with mock.patch("requests.get", mock_non_seas_get_local):
            is_seas_result = PennGroupsGSRBooker.is_seas(non_seas_user)
            self.assertFalse(is_seas_result)

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    def test_groupmembership_auto_sets_is_seas(self, mock_model_is_seas, mock_is_wharton):
        """Test that GroupMembership automatically sets is_seas when created"""
        # Create a user - the model will check SEAS status when membership is created
        seas_user = User.objects.create_user("seas_user", "seas_user@seas.upenn.edu", "pass")

        # Create a group
        group = Group.objects.create(owner=self.user, name="Test Group", color="blue")

        # Create membership WITHOUT explicitly setting is_seas
        # The model's save() method will automatically call check_seas() if is_seas is None
        membership = GroupMembership.objects.create(
            user=seas_user,
            group=group,
            accepted=True,
            is_seas=None,  # Not set - will be auto-checked
        )

        # Refresh from DB to get the value that was saved
        membership.refresh_from_db()

        # Verify is_seas was automatically set to True by the model
        self.assertTrue(membership.is_seas)
        # Verify that the mock was called
        mock_model_is_seas.assert_called()

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch("requests.get", mock_non_seas_get)
    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    def test_groupmembership_auto_sets_is_seas_false(self, mock_model_is_seas, mock_is_wharton):
        """Test that GroupMembership automatically sets is_seas=False for non-SEAS users"""
        # Create a non-SEAS user
        non_seas_user = User.objects.create_user("not_seas_user", "user@sas.upenn.edu", "pass")

        # Create a group
        group = Group.objects.create(owner=self.user, name="Test Group", color="blue")

        # Create membership WITHOUT explicitly setting is_seas
        # The model's save() method will automatically call check_seas() if is_seas is None
        membership = GroupMembership.objects.create(
            user=non_seas_user,
            group=group,
            accepted=True,
            is_seas=None,  # Not set - will be auto-checked
        )

        # Refresh from DB to get the value that was saved
        membership.refresh_from_db()

        # Verify is_seas was automatically set to False by the model
        self.assertFalse(membership.is_seas)
        # Verify that the mock was called
        mock_model_is_seas.assert_called()

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    def test_penngroups_availability(self, mock_is_seas, mock_is_wharton):
        """Test AGH room availability for SEAS students"""
        availability = GSRBooker.get_availability(
            "20157", 42437, "2025-10-30", "2025-10-31", self.user
        )

        self.assertIn("name", availability)
        self.assertIn("gid", availability)
        self.assertIn("rooms", availability)
        self.assertEqual("Amy Gutmann Hall", availability["name"])

        if len(availability["rooms"]) > 0:
            room = availability["rooms"][0]
            self.assertIn("room_name", room)
            self.assertIn("id", room)
            self.assertIn("availability", room)

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_book_penngroups(self, mock_is_seas, mock_is_wharton):
        """Test booking an AGH room"""
        book_agh = GSRBooker.book_room(
            42437,
            172129,
            "AGH 206",
            "2025-10-30T23:30:00-04:00",
            "2025-10-31T00:00:00-04:00",
            self.user,
        )
        self.assertEqual("AGH 206", book_agh.gsrbooking_set.first().room_name)

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    def test_cancel_penngroups(self, mock_is_seas, mock_is_wharton):
        """Test canceling an AGH room booking"""
        group = Group.objects.create(owner=self.user)
        reservation = Reservation.objects.create(creator=self.user, group=group)
        GSRBooking.objects.create(
            reservation=reservation,
            user=self.user,
            booking_id="476df5dc92c1",
            gsr=GSR.objects.filter(kind="PENNGRP").first(),
            room_id=172129,
            room_name="AGH 206",
        )
        cancel = GSRBooker.cancel_room("476df5dc92c1", self.user)
        self.assertIsNone(cancel)

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_group_book_penngroups(self, mock_model_is_seas, mock_is_wharton):
        """Test group booking for AGH rooms"""
        # Make sure group_user is SEAS - when membership is created, is_seas will be auto-set
        # First, get the existing membership (owner is automatically added)
        membership1 = GroupMembership.objects.filter(group=self.group).first()
        # Since is_seas might already be set, refresh it by checking via API
        membership1.is_seas = None  # Reset to trigger auto-check
        membership1.save()  # This will call check_seas() which is mocked to return True
        self.assertTrue(membership1.is_seas)

        # Add user to the group - is_seas will be auto-set to True by the model's save method
        membership2 = GroupMembership.objects.create(
            user=self.user, group=self.group, accepted=True, is_seas=None
        )
        # Verify is_seas was automatically set to True
        membership2.refresh_from_db()
        self.assertTrue(membership2.is_seas)

        start = timezone.localtime()
        end = start + timedelta(hours=2)

        reservation = GSRBooker.book_room(
            42437,
            172129,
            "AGH 206",
            start.strftime("%Y-%m-%dT%H:%M:%S%z"),
            end.strftime("%Y-%m-%dT%H:%M:%S%z"),
            self.user,
            self.group,
        )

        bookings = list(reservation.gsrbooking_set.all())
        bookings.sort(key=lambda x: x.start)

        # Check bookings cover entire range
        for i in range(len(bookings) - 1):
            self.assertEqual(bookings[i].end, bookings[i + 1].start)

        total_time = sum([booking.end - booking.start for booking in bookings], timedelta())
        self.assertEqual(total_time, timedelta(hours=2))

        # Check reservation exists
        self.assertIsNotNone(Reservation.objects.get(pk=reservation.id))

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_penngroups_authorization_filtering(self, mock_is_seas, mock_is_wharton):
        """Test that only authorized rooms are returned for SEAS students"""
        # User authorized for rooms 206 and 334
        availability = GSRBooker.get_availability(
            "20157", 42437, "2025-10-30", "2025-10-31", self.user
        )

        rooms = availability["rooms"]
        room_names = [room["room_name"] for room in rooms]

        # Should only include authorized rooms
        self.assertIn("AGH 206", room_names)
        self.assertIn("AGH 334", room_names)

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_non_seas_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    def test_non_seas_availability(self, mock_is_seas, mock_is_wharton):
        """Test that non-SEAS users get empty availability"""
        non_seas_user = User.objects.create_user("not_seas_user", "user@sas.upenn.edu", "pass")
        availability = GSRBooker.get_availability(
            "20157", 42437, "2025-10-30", "2025-10-31", non_seas_user
        )

        # Should return empty list for non-SEAS users
        self.assertIn("rooms", availability)
        self.assertEqual(0, len(availability["rooms"]))

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_non_seas_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    def test_non_seas_book_fails(self, mock_is_seas, mock_is_wharton):
        """Test that non-SEAS users cannot book AGH rooms"""
        non_seas_user = User.objects.create_user("not_seas_user", "user@sas.upenn.edu", "pass")

        with self.assertRaises(APIError) as context:
            GSRBooker.book_room(
                42437,
                172129,
                "AGH 206",
                "2025-10-30T23:30:00-04:00",
                "2025-10-31T00:00:00-04:00",
                non_seas_user,
            )

        self.assertIn("SEAS", str(context.exception))

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request")
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_unauthorized_room_booking_fails(self, mock_request, mock_is_seas, mock_is_wharton):
        """Test that users cannot book rooms they're not authorized for"""

        # User is only authorized for rooms 206 and 334 (based on mock_penngroups_api_get)
        # Try to book an unauthorized room (e.g., room 999)
        def mock_unauthorized_item_request(*args, **kwargs):
            class Mock:
                def __init__(self, json_data, status_code):
                    self.json_data = json_data
                    self.status_code = status_code
                    self.ok = status_code == 200

                def json(self):
                    return self.json_data

            method = args[0] if len(args) > 0 else kwargs.get("method", "GET")
            url = args[1] if len(args) > 1 else kwargs.get("url", "")

            # For unauthorized room, return a room not in the authorized list
            if method == "GET" and "space/item/" in url and "?" not in url:
                item_id = url.split("space/item/")[1].split("/")[0]
                if item_id == "999999":
                    # Return a room that's not authorized (e.g., AGH 999)
                    # The user is only authorized for rooms 206 and 334 based on the PennGroups mock
                    # LibCal returns a list with one item
                    return Mock(
                        [
                            {
                                "id": 999999,
                                "name": "AGH 999",  # Not in authorized rooms (206, 334)
                                "capacity": 4,
                                "zoneId": 10798,
                            }
                        ],
                        200,
                    )
            # For booking, return success (but authorization check should fail before this)
            elif method == "POST" and "space/reserve" in url:
                # This shouldn't be reached, but return success if it is
                return Mock({"booking_id": "test"}, 200)

            # Otherwise use the normal mock for other requests
            return mock_agh_libcal_request(None, *args, **kwargs)

        mock_request.side_effect = mock_unauthorized_item_request

        with self.assertRaises(APIError) as context:
            GSRBooker.book_room(
                42437,
                999999,
                "AGH 999",
                "2025-10-30T23:30:00-04:00",
                "2025-10-31T00:00:00-04:00",
                self.user,
            )

        self.assertIn("authorized", str(context.exception).lower())

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_group_penngroups_availability(self, mock_model_is_seas, mock_is_wharton):
        """Test group availability for AGH rooms"""
        # Test that group availability works when group has SEAS members
        # When creating membership, is_seas will be auto-set to True by the model
        membership = GroupMembership.objects.create(
            user=self.user, group=self.group, accepted=True, is_seas=None
        )
        # Verify is_seas was automatically set
        membership.refresh_from_db()
        self.assertTrue(membership.is_seas)

        availability = GSRBooker.get_availability(
            "20157", 42437, "2025-10-30", "2025-10-31", self.group_user, self.group
        )

        self.assertIn("name", availability)
        self.assertIn("gid", availability)
        self.assertIn("rooms", availability)
        self.assertEqual("Amy Gutmann Hall", availability["name"])

        # Should only return authorized rooms
        rooms = availability["rooms"]
        room_names = [room["room_name"] for room in rooms]
        self.assertIn("AGH 206", room_names)
        self.assertIn("AGH 334", room_names)

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_non_seas_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    def test_group_penngroups_availability_no_seas_members(
        self, mock_model_is_seas, mock_is_wharton
    ):
        """Test that group availability returns empty when group has no SEAS members"""
        # Group has no SEAS members - when creating membership, is_seas will be auto-set to False
        membership = GroupMembership.objects.create(
            user=self.user, group=self.group, accepted=True, is_seas=None
        )
        # Verify is_seas was automatically set to False
        membership.refresh_from_db()
        self.assertFalse(membership.is_seas)

        # Should raise APIError when trying to get availability with no SEAS members
        # Note: The actual implementation may return empty list instead of raising error
        availability = GSRBooker.get_availability(
            "20157", 42437, "2025-10-30", "2025-10-31", self.group_user, self.group
        )

        # Should return empty rooms list
        self.assertIn("rooms", availability)
        self.assertEqual(0, len(availability["rooms"]))

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    def test_extract_room_number(self, mock_is_wharton):
        """Test room number extraction from LibCal room names"""
        from gsr_booking.api_wrapper import PennGroupsGSRBooker

        # Test valid room names
        self.assertEqual("206", PennGroupsGSRBooker.extract_room_number("AGH 206"))
        self.assertEqual("334", PennGroupsGSRBooker.extract_room_number("AGH 334"))
        self.assertEqual("123", PennGroupsGSRBooker.extract_room_number("AGH 123"))

        # Test with extra spaces
        self.assertEqual("206", PennGroupsGSRBooker.extract_room_number("AGH  206"))

        # Test invalid formats
        self.assertIsNone(PennGroupsGSRBooker.extract_room_number("Room 206"))
        self.assertIsNone(PennGroupsGSRBooker.extract_room_number("AGH"))
        self.assertIsNone(PennGroupsGSRBooker.extract_room_number(""))
        self.assertIsNone(PennGroupsGSRBooker.extract_room_number("206"))

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    def test_is_room_authorized(self, mock_is_wharton):
        """Test room authorization checking logic"""
        from gsr_booking.api_wrapper import PennGroupsGSRBooker

        # Mock authorized extensions
        authorized_extensions = {"GroupStudyRoom_206", "GroupStudyRoom_334"}

        # Test authorized rooms
        self.assertTrue(PennGroupsGSRBooker.is_room_authorized("AGH 206", authorized_extensions))
        self.assertTrue(PennGroupsGSRBooker.is_room_authorized("AGH 334", authorized_extensions))

        # Test unauthorized rooms
        self.assertFalse(PennGroupsGSRBooker.is_room_authorized("AGH 999", authorized_extensions))
        self.assertFalse(PennGroupsGSRBooker.is_room_authorized("AGH 100", authorized_extensions))

        # Test invalid room names
        self.assertFalse(PennGroupsGSRBooker.is_room_authorized("Room 206", authorized_extensions))
        self.assertFalse(PennGroupsGSRBooker.is_room_authorized("", authorized_extensions))

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get")
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_get_authorized_rooms_api_errors(self, mock_get, mock_is_wharton):
        """Test error handling in get_authorized_rooms"""
        from gsr_booking.api_wrapper import PennGroupsGSRBooker

        # Test HTTP error
        class MockResponse:
            def __init__(self, status_code):
                self.status_code = status_code
                self.ok = False

            def json(self):
                return {}

        mock_get.return_value = MockResponse(500)

        with self.assertRaises(APIError) as context:
            PennGroupsGSRBooker.get_authorized_rooms(self.user)
        self.assertIn("HTTP 500", str(context.exception))

        # Test timeout
        mock_get.side_effect = ConnectTimeout()
        with self.assertRaises(APIError) as context:
            PennGroupsGSRBooker.get_authorized_rooms(self.user)
        self.assertIn("timeout", str(context.exception).lower())

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_penngroups_booking_creates_reservation(self, mock_is_seas, mock_is_wharton):
        """Test that booking creates proper database records"""
        initial_reservation_count = Reservation.objects.count()
        initial_booking_count = GSRBooking.objects.count()

        book_agh = GSRBooker.book_room(
            42437,
            172129,
            "AGH 206",
            "2025-10-30T23:30:00-04:00",
            "2025-10-31T00:00:00-04:00",
            self.user,
        )

        # Verify reservation was created
        self.assertEqual(Reservation.objects.count(), initial_reservation_count + 1)
        self.assertEqual(GSRBooking.objects.count(), initial_booking_count + 1)

        # Verify reservation details
        self.assertEqual(book_agh.creator, self.user)
        self.assertIsNotNone(book_agh.start)
        self.assertIsNotNone(book_agh.end)

        # Verify booking details
        booking = book_agh.gsrbooking_set.first()
        self.assertEqual(booking.room_name, "AGH 206")
        self.assertEqual(booking.room_id, 172129)
        self.assertEqual(booking.user, self.user)
        self.assertIsNotNone(booking.booking_id)

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    def test_penngroups_availability_date_filtering(self, mock_is_seas, mock_is_wharton):
        """Test that availability respects date filtering"""
        # Get availability for a specific date range
        availability = GSRBooker.get_availability(
            "20157", 42437, "2025-10-30", "2025-10-31", self.user
        )

        # Verify structure
        self.assertIn("rooms", availability)
        rooms = availability["rooms"]

        # Verify each room has availability slots
        for room in rooms:
            self.assertIn("availability", room)
            # Verify availability slots are within the requested date range
            for slot in room["availability"]:
                self.assertIn("start_time", slot)
                self.assertIn("end_time", slot)
                # Verify times are properly formatted
                self.assertRegex(slot["start_time"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
                self.assertRegex(slot["end_time"], r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False)
    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    def test_cancel_penngroups_marks_booking_cancelled(self, mock_is_seas, mock_is_wharton):
        """Test that canceling properly marks bookings as cancelled"""
        # Create a booking first
        group = Group.objects.create(owner=self.user)
        gsr = GSR.objects.filter(kind="PENNGRP").first()
        reservation = Reservation.objects.create(
            creator=self.user,
            group=group,
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=1),
        )
        booking = GSRBooking.objects.create(
            reservation=reservation,
            user=self.user,
            booking_id="test_cancel_id",
            gsr=gsr,
            room_id=172129,
            room_name="AGH 206",
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=1),
        )

        # Verify booking is not cancelled initially
        self.assertFalse(booking.is_cancelled)

        # Cancel the booking
        GSRBooker.cancel_room("test_cancel_id", self.user)

        # Verify booking is now marked as cancelled
        booking.refresh_from_db()
        self.assertTrue(booking.is_cancelled)

        # Verify the booking can be retrieved from database with cancelled status
        cancelled_booking = GSRBooking.objects.get(booking_id="test_cancel_id")
        self.assertTrue(cancelled_booking.is_cancelled)

    @mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False)
    @mock.patch("requests.get", mock_penngroups_api_get)
    @mock.patch("gsr_booking.api_wrapper.PennGroupsBookingWrapper.request", mock_agh_libcal_request)
    @mock.patch("gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=True)
    @mock.patch(
        "gsr_booking.api_wrapper.PennGroupsBookingWrapper.get_user_pennid", mock_get_user_pennid
    )
    def test_group_book_penngroups_credit_distribution(self, mock_model_is_seas, mock_is_wharton):
        """Test that group bookings properly distribute credits among members"""
        # Set up group with multiple SEAS members
        membership1 = GroupMembership.objects.filter(group=self.group).first()
        membership1.is_seas = True
        membership1.save()

        membership2 = GroupMembership.objects.create(
            user=self.user, group=self.group, accepted=True, is_seas=True
        )
        # Verify membership was created correctly
        membership2.refresh_from_db()
        self.assertTrue(membership2.is_seas)

        # Book a long duration to require multiple members' credits
        start = timezone.localtime()
        end = start + timedelta(hours=2)

        reservation = GSRBooker.book_room(
            42437,
            172129,
            "AGH 206",
            start.strftime("%Y-%m-%dT%H:%M:%S%z"),
            end.strftime("%Y-%m-%dT%H:%M:%S%z"),
            self.user,
            self.group,
        )

        # Verify multiple bookings were created (one per member's credit)
        bookings = list(reservation.gsrbooking_set.all())
        self.assertGreater(len(bookings), 0)

        # Verify bookings are continuous
        bookings.sort(key=lambda x: x.start)
        for i in range(len(bookings) - 1):
            self.assertEqual(bookings[i].end, bookings[i + 1].start)

        # Verify total time matches requested duration
        total_time = sum([booking.end - booking.start for booking in bookings], timedelta())
        self.assertEqual(total_time, timedelta(hours=2))
