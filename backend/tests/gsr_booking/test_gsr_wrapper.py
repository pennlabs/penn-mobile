import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
# from django.urls import reverse
from rest_framework.test import APIClient

from gsr_booking.api_wrapper import BookingWrapper


User = get_user_model()


def mock_requests_get(obj, *args, **kwargs):
    class Mock:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    url = args[1]
    print(url)

    if "wharton" in url and "privileges" in url: # is wharton check
        file_path = "tests/gsr_booking/api_is_wharton.json"
    elif "wharton" in url and "student_reserve" in url: # wharton booking
        file_path = "tests/gsr_booking/api_wharton_book.json"
    elif "wharton" in url and "availability" in url: # wharton availability
        file_path = "tests/gsr_booking/api_wharton_availability.json"
    elif "wharton" in url and "reservations" in url:
        file_path = "tests/gsr_booking/api_wharton_reservations.json"
    elif "wharton" in url and "cancel" in url:
        file_path = "tests/gsr_booking/api_wharton_cancel.json"


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
        self.assertIn('name', availability)
        self.assertIn('gid', availability)
        self.assertIn('rooms', availability)
        self.assertIn('room_name', availability['rooms'][0])
        self.assertIn('id', availability['rooms'][0])
        self.assertIn('availability', availability['rooms'][0])

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get)
    def test_book_wharton(self):
        book_wharton = self.bw.book_room(
            1, 94, "241", "2021-12-05T16:00:00-05:00", "2021-12-05T16:30:00-05:00", self.user
        )
        self.assertIsNone(book_wharton)

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get)
    def test_wharton_reservations(self):
        reservations = self.bw.WLW.get_reservations(self.user, [])
        self.assertTrue(isinstance(reservations, list))
        self.assertIn('booking_id', reservations[0])
        self.assertIn('gsr', reservations[0])

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get)
    def test_cancel_wharton(self):
        cancel = self.bw.cancel_room("987654", self.user)
        self.assertIsNone(cancel)