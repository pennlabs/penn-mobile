import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from presence.models import PresenceOptIn


User = get_user_model()


class TestOptInView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(403, self.client.get("/presence/opt-in/").status_code)
        self.assertEqual(403, self.client.post("/presence/opt-in/").status_code)

    def test_defaults_to_opted_out(self):
        response = self.client.get("/presence/opt-in/")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"opted_in": False}, json.loads(response.content))

    def test_opt_in(self):
        response = self.client.post("/presence/opt-in/", {"opted_in": True}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"opted_in": True}, json.loads(response.content))
        self.assertTrue(self.user.presence_opt_in.opted_in)

    def test_opt_back_out(self):
        self.client.post("/presence/opt-in/", {"opted_in": True}, format="json")
        self.client.post("/presence/opt-in/", {"opted_in": False}, format="json")
        response = self.client.get("/presence/opt-in/")
        self.assertEqual({"opted_in": False}, json.loads(response.content))
        self.assertEqual(1, PresenceOptIn.objects.count())

    def test_non_boolean_rejected(self):
        for bad in ["yes", 1, None]:
            response = self.client.post("/presence/opt-in/", {"opted_in": bad}, format="json")
            self.assertEqual(400, response.status_code)
        self.assertEqual(400, self.client.post("/presence/opt-in/", {}, format="json").status_code)
        self.assertFalse(PresenceOptIn.objects.filter(user=self.user, opted_in=True).exists())
