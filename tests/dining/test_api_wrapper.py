from django.test import TestCase

from dining.api_wrapper import APIError, dining_request, headers


class TestHeaders(TestCase):
    def test(self):

        response = headers()

        self.assertEqual(len(response), 2)
        self.assertTrue("Authorization-Bearer" in response.keys())
        self.assertTrue("Authorization-Token" in response.keys())


class TestRequest(TestCase):
    def test(self):

        response = headers()
        response["Authorization-Bearer"] = "qwertyuiopasdfghjklzxcvbnm"

        try:
            dining_request("https://esb.isc-seo.upenn.edu/8091/open_data/dining/v2/?service=venues")
        except APIError as e:
            self.assertTrue("Request to" in str(e.args))
            self.assertTrue("returned 401" in str(e.args))
