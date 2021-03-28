from django.test import TestCase

from dining.api_wrapper import headers


class TestHeaders(TestCase):
    def test(self):

        response = headers()

        self.assertEqual(len(response), 2)
        self.assertTrue("Authorization-Bearer" in response.keys())
        self.assertTrue("Authorization-Token" in response.keys())
