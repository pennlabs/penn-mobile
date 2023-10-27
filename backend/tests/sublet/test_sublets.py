import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from django.utils import timezone
from rest_framework.test import APIClient

from sublet.models import Amenity, Offer, Sublet, SubletImage

User = get_user_model()


class TestSublets(TestCase):
    """Tests Create/Update/Retrieve/List for sublets"""

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        test_user = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        for i in range(1, 6):
            Amenity.objects.create(name=f"Amenity{str(i)}")
        with open("tests/sublet/mock_sublets.json") as data:
            data = json.load(data)
            sublet1 = Sublet.objects.create(subletter=self.user, **data[0])
            sublet2 = Sublet.objects.create(subletter=test_user, **data[1])

    def test_create_sublet(self):
        # Create a new sublet using the serializer
        payload = {
            "title": "Test Sublet1",
            "address": "1234 Test Street",
            "beds": 2,
            "baths": 1,
            "description": "This is a test sublet.",
            "external_link": "https://example.com",
            "min_price": 100,
            "max_price": 500,
            "expires_at": "2024-02-01T10:48:02-05:00",
            "start_date": "2024-04-09",
            "end_date": "2024-08-07",
            "amenities": ["Amenity1", "Amenity2"],
        }

        response = self.client.post("/properties/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(2, res_json["beds"])
        self.assertEqual("Test Sublet1", res_json["title"])
        # sublet = Sublet.objects.get(title="Test Sublet1")
        # self.assertEqual(sublet.beds, 2)

    def test_update_sublet(self):
        # Create a sublet to be updated
        sublet = Sublet.objects.create(
            title="Old Title",
            address="1234 Old Street",
            beds=2,
            baths=1,
            description="This is an old sublet.",
            external_link="https://example.com",
            min_price=100,
            max_price=500,
            expires_at="2024-02-01T10:48:02-05:00",
            start_date="2024-04-09",
            end_date="2024-08-07",
            subletter=self.user,
        )

        # Update the sublet using the serializer
        data = {"title": "New Title", "beds": 3}

        response = self.client.patch(f"/properties/{sublet.id}/", data)
        res_json = json.loads(response.content)
        self.assertEqual(3, res_json["beds"])
        self.assertEqual(self.id, res_json["id"])
        self.assertEqual("New Title", Sublet.objects.get(id=self.id).title)
        self.assertEqual("New Title", res_json["title"])

    def test_browse_sublets(self):
        payload = {
            "title": "Test Sublet1",
            "address": "1234 Test Street",
            "beds": 2,
            "baths": 1,
            "description": "This is a test sublet.",
            "external_link": "https://example.com",
            "min_price": 100,
            "max_price": 500,
            "expires_at": "2024-02-01T10:48:02-05:00",
            "start_date": "2024-04-09",
            "end_date": "2024-08-07",
            "amenities": ["Amenity1", "Amenity2"],
        }
        self.client.post("/properties/", payload)
        response = self.client.get("/properties/")
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual(2, Sublet.objects.all().count())

    def test_browse_sublet(self):
        # browse single sublet by id
        pass


class TestOffers(TestCase):
    """Tests Create/Delete/List for offers"""

    # TODO: test create offer fails when offer is duplicate
    # TODO: delete offer fails when offer doesn't exist

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

    def test_delete_offer(self):
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        self.client.post("/sublet/properties/2/offers/", payload)
        # TODO: Uncomment this once proper handling is done for offer deletion not found
        # offers_count = Offer.objects.all().count()
        # self.client.delete("/sublet/properties/1/offers/")
        # offers = Offer.objects.all()
        # self.assertEqual(offers_count, offers.count())
        self.client.delete("/sublet/properties/2/offers/")
        self.assertFalse(
            Offer.objects.filter(user=self.user, sublet=Sublet.objects.get(pk=2)).exists()
        )

    def test_get_offers_property(self):
        response = self.client.get("/sublet/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(0, len(res_json))
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        self.client.post("/sublet/properties/1/offers/", payload)
        response = self.client.get("/sublet/properties/1/offers/")
        self.assertEqual(1, len(json.loads(response.content)))
        Offer.objects.create(
            user=User.objects.get(pk=2),
            sublet=Sublet.objects.get(pk=1),
            email="offer2@seas.upenn.edu",
            phone_number="0987654321",
            message="Message2",
        )
        response = self.client.get("/sublet/properties/1/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        # TODO: this is really ugly, will clean up later haha
        offer = res_json[0]
        self.assertEqual(offer["email"], "offer@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "1234567890")
        self.assertEqual(offer["message"], "Message")
        self.assertEqual(offer["user"], self.user.id)
        self.assertEqual(offer["sublet"], 1)
        self.assertEqual(offer["id"], 1)
        self.assertIsNotNone(offer["created_date"])
        offer = res_json[1]
        self.assertEqual(offer["email"], "offer2@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "0987654321")
        self.assertEqual(offer["message"], "Message2")
        self.assertEqual(offer["user"], 2)
        self.assertEqual(offer["sublet"], 1)
        self.assertEqual(offer["id"], 2)
        self.assertIsNotNone(offer["created_date"])

    def test_get_offer_user(self):
        response = self.client.get("/sublet/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(0, len(res_json))
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        self.client.post("/sublet/properties/1/offers/", payload)
        response = self.client.get("/sublet/offers/")
        self.assertEqual(1, len(json.loads(response.content)))
        payload = {
            "email": "offer2@seas.upenn.edu",
            "phone_number": "0987654321",
            "message": "Message2",
        }
        self.client.post("/sublet/properties/2/offers/", payload)
        response = self.client.get("/sublet/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        # TODO: clean up
        offer = res_json[0]
        self.assertEqual(offer["email"], "offer@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "1234567890")
        self.assertEqual(offer["message"], "Message")
        self.assertEqual(offer["user"], self.user.id)
        self.assertEqual(offer["sublet"], 1)
        self.assertEqual(offer["id"], 1)
        self.assertIsNotNone(offer["created_date"])
        offer = res_json[1]
        self.assertEqual(offer["email"], "offer2@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "0987654321")
        self.assertEqual(offer["message"], "Message2")
        self.assertEqual(offer["user"], 1)
        self.assertEqual(offer["sublet"], 2)
        self.assertEqual(offer["id"], 2)
        self.assertIsNotNone(offer["created_date"])


class TestFavorites(TestCase):
    """Tests Create/Delete/List for favorites"""

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

    def test_create_favorite(self):
        response = self.client.post("/sublet/properties/2/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=2).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=1).exists())
        # TODO: Write case for erroring out on already favorited once that's been implemented
        response = self.client.post("/sublet/properties/1/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=2).exists())
        self.assertTrue(self.user.sublets_favorited.filter(pk=1).exists())

    def test_delete_favorite(self):
        self.client.post("/sublet/properties/2/favorites/")
        self.client.post("/sublet/properties/1/favorites/")
        response = self.client.delete("/sublet/properties/1/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=2).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=1).exists())
        response = self.client.post("/sublet/properties/1/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=2).exists())
        self.assertTrue(self.user.sublets_favorited.filter(pk=1).exists())
        response = self.client.delete("/sublet/properties/1/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=2).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=1).exists())
        response = self.client.delete("/sublet/properties/2/favorites/")
        self.assertFalse(self.user.sublets_favorited.filter(pk=2).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=1).exists())

    def test_get_favorite_user(self):
        self.client.post("/sublet/properties/2/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 1)
        self.assertEqual(res_json[0]["id"], 2)
        self.client.post("/sublet/properties/1/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 2)
        self.client.delete("/sublet/properties/2/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 1)
        self.assertEqual(res_json[0]["id"], 1)
