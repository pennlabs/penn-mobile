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

    if "privileges" in url:
        # is_wharton
        file_path = "tests/gsr_booking/api_is_wharton.json"
    # if "reservations" in url
    # else:
    #     # make elifs and change file paths here
    #     pass
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
    def test_book_wharton(self):
        pass
        # gid = 1 indicates wharton
        # book_wharton = self.bw.book_room(
        #     1, 94, "241", "2021-12-05T16:00:00-05:00", "2021-12-05T16:30:00-05:00", self.user
        # )

        # print("hi")

    # @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request",
    # mock_requests_get, spec=['hi'])
    # def test_is_wharton(self):
    #     #response = self.client.get(reverse("is-wharton"))

    #     res_json = json.loads(response.content)
    #     self.assertFalse(res_json["is_wharton"])

    # @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request",
    # mock_requests_get, spec=['hi'])
    # def test_cancel(self):
    #     #response = self.client.get(reverse("cancel"))
    #     res_json = json.loads(response.content)
    #     #self.assertFalse(res_json["is_wharton"])
