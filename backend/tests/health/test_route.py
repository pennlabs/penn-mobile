from django.test import TestCase


class HealthTestCase(TestCase):
    def test_health(self):
        resp = self.client.get("/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"message": "OK"})
