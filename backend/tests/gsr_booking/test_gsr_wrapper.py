"""
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from gsr_booking.api_wrapper import BookingWrapper
from gsr_booking.models import GSR, Group, GSRBooking, Reservation


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


class TestBookingWrapper(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.bw = BookingWrapper()

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get)
    def test_is_wharton(self):
        self.assertFalse(self.bw.is_wharton(self.user.username))

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get)
    def test_wharton_availability(self):
        availability = self.bw.get_availability("JMHH", 1, "2021-01-07", "2022-01-08", self.user)
        self.assertIn("name", availability)
        self.assertIn("gid", availability)
        self.assertIn("rooms", availability)
        self.assertIn("room_name", availability["rooms"][0])
        self.assertIn("id", availability["rooms"][0])
        self.assertIn("availability", availability["rooms"][0])

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get)
    def test_book_wharton(self):
        book_wharton = self.bw.book_room(
            1, 94, "241", "2021-12-05T16:00:00-05:00", "2021-12-05T16:30:00-05:00", self.user
        )
        self.assertIsNone(book_wharton)

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get)
    def test_wharton_reservations(self):
        reservations = self.bw.WLW.get_reservations(self.user)
        self.assertTrue(isinstance(reservations, list))
        self.assertIn("booking_id", reservations[0])
        self.assertIn("gsr", reservations[0])

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get)
    def test_cancel_wharton(self):
        cancel = self.bw.cancel_room("987654", self.user)
        self.assertIsNone(cancel)

    @mock.patch("gsr_booking.api_wrapper.LibCalWrapper.request", mock_requests_get)
    def test_libcal_availability(self):
        availability = self.bw.get_availability("1086", 1889, "2021-01-07", "2022-01-08", self.user)
        self.assertIn("name", availability)
        self.assertIn("gid", availability)
        self.assertIn("rooms", availability)
        self.assertIn("room_name", availability["rooms"][0])
        self.assertIn("id", availability["rooms"][0])
        self.assertIn("availability", availability["rooms"][0])

    @mock.patch("gsr_booking.api_wrapper.LibCalWrapper.request", mock_requests_get)
    def test_book_libcal(self):
        book_libcal = self.bw.book_room(
            1889,
            7192,
            "VP WIC Booth 01",
            "2021-12-05T16:00:00-05:00",
            "2021-12-05T16:30:00-05:00",
            self.user,
        )
        self.assertIsNone(book_libcal)

    @mock.patch(
        "gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get
    )  # purposefully wharton request here
    def test_libcal_reservations(self):
        reservations = self.bw.get_reservations(self.user)
        self.assertTrue(isinstance(reservations, list))
        self.assertIn("booking_id", reservations[0])
        self.assertIn("gsr", reservations[0])

    @mock.patch("gsr_booking.api_wrapper.LibCalWrapper.request", mock_requests_get)
    def test_cancel_libcal(self):
        group = Group.objects.create(owner=self.user)
        reservation = Reservation.objects.create(creator=self.user, group=group)
        GSRBooking.objects.create(
            reservation=reservation,
            user=self.user,
            booking_id="123",
            gsr=GSR.objects.all().first(),
            room_id=1,
            room_name="room",
        )
        cancel = self.bw.cancel_room("123", self.user)
        self.assertIsNone(cancel)
"""
