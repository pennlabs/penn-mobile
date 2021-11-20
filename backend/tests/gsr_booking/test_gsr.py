import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


User = get_user_model()


class TestGSRs(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_user)

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

    def test_get_wharton(self):
        response = self.client.get(reverse("is-wharton"))
        res_json = json.loads(response.content)
        self.assertFalse(res_json["is_wharton"])
