"""
import json

import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest import mock

User = get_user_model()

def mock_requests_get(className, *args, **kwargs):
    class Mock:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    url = args[1]

    if "priveleges" in url:
        file_path = "tests/gsr_booking/is_wharton.json"
    else:
        # make elifs and change file paths here
        pass
    with open(file_path) as data:
        return Mock(json.load(data), 200)

User = get_user_model()

# @mock.patch("requests.post", mock_requests_get)
class TestBookingWrapper(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get, spec=['hi'])
    def test_is_wharton(self):
        #response = self.client.get(reverse("is-wharton"))

        res_json = json.loads(response.content)
        self.assertFalse(res_json["is_wharton"])

    @mock.patch("gsr_booking.api_wrapper.WhartonLibWrapper.request", mock_requests_get, spec=['hi'])
    def test_cancel(self):
        #response = self.client.get(reverse("cancel"))
        res_json = json.loads(response.content)
        #self.assertFalse(res_json["is_wharton"])



# class TestGSRs(TestCase):
#     def setUp(self):
#         call_command("load_gsrs")
#         self.test_user = User.objects.create_user("user", "user@a.com", "user")
#         self.client = APIClient()
#         self.client.force_authenticate(user=self.test_user)

#     def test_get_location(self):
#         response = self.client.get(reverse("locations"))
#         res_json = json.loads(response.content)
#         for entry in res_json:
#             if entry["id"] == 1:
#                 self.assertEquals(entry["name"], "Huntsman")
#             if entry["id"] == 2:
#                 self.assertEquals(entry["name"], "Academic Research")
#             if entry["id"] == 3:
#                 self.assertEquals(entry["name"], "Weigle")

#     def test_get_wharton(self):
#         response = self.client.get(reverse("is-wharton"))
#         res_json = json.loads(response.content)
#         self.assertFalse(res_json["is_wharton"])
"""
