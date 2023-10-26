import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from sublet.models import Amenity, Offer, Sublet, SubletImage

User = get_user_model()


class TestSublets(TestCase):
    """Tests Create/Update/Retrieve/List for sublets"""

    # @Ashley test cases for sublet creation/browsing/searching go here please :)
    pass


class TestOffers(TestCase):
    """Tests Create/Delete/List for offers"""

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        test_user = User.objects.create_user("user1", "user")
        for i in range(1, 6):
            Amenity.objects.create(name=f"Amenity{str(i)}")
        # TODO: Not sure how to add these amenities to the sublets, but not important for now
        with open("tests/sublet/mock_sublets.json") as data:
            data = json.load(data)
            sublet1 = Sublet.objects.create(subletter=self.user, **data[0])
            sublet2 = Sublet.objects.create(subletter=test_user, **data[1])

    def test_create_offer(self):
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        response = self.client.post("/sublet/properties/2/offers/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(res_json["email"], payload["email"])
        self.assertEqual(res_json["phone_number"], payload["phone_number"])
        self.assertEqual(res_json["message"], payload["message"])
        self.assertEqual(res_json["user"], self.user.id)
        self.assertEqual(res_json["sublet"], 2)
        self.assertEqual(res_json["id"], 1)
        self.assertIn("created_date", res_json)
        offer = Offer.objects.get(pk=1)
        self.assertEqual(offer.email, payload["email"])
        self.assertEqual(offer.phone_number, payload["phone_number"])
        self.assertEqual(offer.message, payload["message"])
        self.assertEqual(offer.user, self.user)
        self.assertEqual(offer.sublet, Sublet.objects.get(pk=2))
        self.assertEqual(offer.id, 1)
        self.assertIsNotNone(offer.created_date)

    # def test_delete_offer


class TestFavorites(TestCase):
    """Tests Create/Delete/List for favorites"""

    pass
