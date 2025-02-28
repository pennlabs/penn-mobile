from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class HealthTestCase(TestCase):
    def test_health(self):
        resp = self.client.get("/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"message": "OK"})
