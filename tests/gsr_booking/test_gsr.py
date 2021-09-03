import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


User = get_user_model()


class TestLocations(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.client = APIClient()

    def test_get(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(reverse("locations"))
        res_json = json.loads(response.content)
        for entry in res_json:
            if entry["id"] == 1:
                self.assertEquals(entry["name"], "Huntsman")
            if entry["id"] == 2:
                self.assertEquals(entry["name"], "Weigle")
