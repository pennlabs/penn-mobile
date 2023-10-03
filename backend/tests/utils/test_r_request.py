from json.decoder import JSONDecodeError
from unittest.mock import patch

from django.test import TestCase

from utils.r_request import RRequest


def raise_decode_error():
    raise JSONDecodeError("Invalid JSON data", "invalid_json", 0)


class RRequestTestCase(TestCase):
    def setUp(self):
        self.url = "https://pennlabs.org"
        self.json = {"data": "data"}
        self.rrequest = RRequest()

    @patch("requests.request")
    def test_successful_request(self, mock_response):
        mock_response.return_value.status_code = 200
        response = self.rrequest.request("get", self.url)
        self.assertEqual(200, response.status_code)

    @patch("requests.request")
    def test_unsuccessful_request(self, mock_response):
        mock_response.return_value.status_code = 400
        mock_response.return_value.content = "Bad Error"
        response = self.rrequest.request("post", self.url, json=self.json)
        self.assertEqual(400, response.status_code)
        self.assertEqual("Bad Error", response.content)

    @patch("requests.request")
    def test_bad_json(self, mock_response):
        mock_response.return_value.status_code = 200
        mock_response.return_value.json = raise_decode_error
        response = self.rrequest.delete(self.url, json=self.json)
        self.assertEqual(200, response.status_code)

    @patch("requests.request")
    def test_get_request(self, mock_response):
        mock_response.return_value.status_code = 200
        response = self.rrequest.get(self.url)
        self.assertEqual(200, response.status_code)

    @patch("requests.request")
    def test_post_request(self, mock_response):
        mock_response.return_value.status_code = 200
        response = self.rrequest.post(self.url, json=self.json)
        self.assertEqual(200, response.status_code)

    @patch("requests.request")
    def test_patch_request(self, mock_response):
        mock_response.return_value.status_code = 200
        response = self.rrequest.patch(self.url)
        self.assertEqual(200, response.status_code)

    @patch("requests.request")
    def test_put_request(self, mock_response):
        mock_response.return_value.status_code = 200
        response = self.rrequest.put(self.url, json=self.json)
        self.assertEqual(200, response.status_code)

    @patch("requests.request")
    def test_delete_request(self, mock_response):
        mock_response.return_value.status_code = 200
        response = self.rrequest.delete(self.url, json=self.json)
        self.assertEqual(200, response.status_code)
