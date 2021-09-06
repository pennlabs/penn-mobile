from django.test import TestCase

from dining.api_wrapper import headers


class TestHeaders(TestCase):
    def test(self):

        response = headers()

        self.assertEqual(len(response), 2)
        self.assertIn("Authorization-Bearer", response.keys())
        self.assertIn("Authorization-Token", response.keys())
