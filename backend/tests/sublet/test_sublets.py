import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from sublet.models import Amenity, Offer, Sublet


# , SubletImage)


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
            Sublet.objects.create(subletter=self.user, **data[0])
            Sublet.objects.create(subletter=test_user, **data[1])

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

        response = self.client.post("/sublet/properties/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(payload["beds"], res_json["beds"])
        self.assertEqual(payload["title"], res_json["title"])
        self.assertIn("created_at", res_json)

    def test_update_sublet(self):
        # Create a sublet to be updated
        payload = {
            "title": "Old Title",
            "address": "1234 Old Street",
            "beds": 2,
            "baths": 1,
            "description": "This is an old sublet.",
            "external_link": "https://example.com",
            "min_price": 100,
            "max_price": 500,
            "expires_at": "2024-02-01T10:48:02-05:00",
            "start_date": "2024-04-09",
            "end_date": "2024-08-07",
            "amenities": ["Amenity1", "Amenity2"],
        }
        self.client.post("/sublet/properties/", payload)
        # Update the sublet using the serializer
        data = {"title": "New Title", "beds": 3}

        response = self.client.patch("/sublet/properties/3/", data)
        res_json = json.loads(response.content)
        self.assertEqual(3, res_json["beds"])
        self.assertEqual(3, Sublet.objects.all().last().id)
        self.assertEqual("New Title", Sublet.objects.get(id=3).title)
        self.assertEqual("New Title", res_json["title"])

    def test_browse_sublets(self):
        response = self.client.get("/sublet/properties/")
        res_json = json.loads(response.content)
        first_length = len(res_json)
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
        self.client.post("/sublet/properties/", payload)
        response = self.client.get("/sublet/properties/")
        res_json = json.loads(response.content)
        self.assertEqual(1+first_length, len(res_json))
        sublet = res_json[-1]
        self.assertEqual(sublet["title"], "Test Sublet1")
        self.assertEqual(sublet["address"], "1234 Test Street")
        self.assertEqual(sublet["beds"], 2)
        self.assertEqual(sublet["baths"], 1)

    def test_browse_sublet(self):
        # browse single sublet by id
        payload = {
            "title": "Test Sublet2",
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
        self.client.post("/sublet/properties/", payload)
        response = self.client.get("/sublet/properties/3/")
        res_json = json.loads(response.content)
        self.assertEqual(res_json["title"], "Test Sublet2")
        self.assertEqual(res_json["address"], "1234 Test Street")
        self.assertEqual(res_json["beds"], 2)
        self.assertEqual(res_json["baths"], 1)

    def test_delete_sublet(self):
        sublets_count = Sublet.objects.all().count()
        self.client.delete("/sublet/properties/1/")
        self.assertEqual(sublets_count-1, Sublet.objects.all().count())
        self.assertFalse(Sublet.objects.filter(id=1).exists())

    def test_amenities(self):
        response = self.client.get("/sublet/amenities/")
        res_json = json.loads(response.content)
        for i in range(1, 6):
            self.assertIn(f"Amenity{i}", res_json)


class TestOffers(TestCase):
    """Tests Create/Delete/List for offers"""

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.test_user = User.objects.create_user("user1", "user")
        for i in range(1, 6):
            Amenity.objects.create(name=f"Amenity{str(i)}")
        # TODO: Not sure how to add these amenities to the sublets, but not important for now
        with open("tests/sublet/mock_sublets.json") as data:
            data = json.load(data)
            self.first_sublet = Sublet.objects.create(subletter=self.user, **data[0])
            self.second_sublet = Sublet.objects.create(subletter=self.test_user, **data[1])

    def test_create_offer(self):
        prop_url = f"/sublet/properties/{str(self.second_sublet.id)}/offers/"
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        self.client.post(prop_url, payload)
        self.assertEqual(self.client.post(prop_url, payload).status_code, 406)
        offer = Offer.objects.get(pk=1)
        offer_list = [offer.email, offer.phone_number, offer.message, offer.user, offer.sublet]
        payload_list = [
            payload["email"],
            payload["phone_number"],
            payload["message"],
            self.user,
            self.second_sublet,
        ]
        for o, p in zip(offer_list, payload_list):
            self.assertEqual(o, p)
        self.assertIsNotNone(offer.id)
        self.assertIsNotNone(offer.created_date)

    def test_delete_offer(self):
        prop_url1 = f"/sublet/properties/{str(self.first_sublet.id)}/offers/"
        prop_url2 = f"/sublet/properties/{str(self.second_sublet.id)}/offers/"
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        self.client.post(prop_url2, payload)
        offers_count = Offer.objects.all().count()
        self.assertEqual(self.client.delete(prop_url1).status_code, 404)
        offers_count_new = Offer.objects.all().count()
        self.assertEqual(offers_count, offers_count_new)
        self.client.delete(prop_url2)
        self.assertFalse(Offer.objects.filter(user=self.user, sublet=self.second_sublet).exists())

    def test_get_offers_property(self):
        response = self.client.get("/sublet/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(0, len(res_json))
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/offers/", payload)
        response = self.client.get(f"/sublet/properties/{str(self.first_sublet.id)}/offers/")
        self.assertEqual(1, len(json.loads(response.content)))
        Offer.objects.create(
            user=self.test_user,
            sublet=self.first_sublet,
            email="offer2@seas.upenn.edu",
            phone_number="0987654321",
            message="Message2",
        )
        response = self.client.get(f"/sublet/properties/{str(self.first_sublet.id)}/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        # TODO: this is really ugly, maybe clean up later haha
        offer = res_json[0]
        self.assertEqual(offer["email"], "offer@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "1234567890")
        self.assertEqual(offer["message"], "Message")
        self.assertEqual(offer["user"], self.user.id)
        self.assertEqual(offer["sublet"], self.first_sublet.id)
        self.assertIsNotNone(offer["id"])
        self.assertIsNotNone(offer["created_date"])
        offer = res_json[1]
        self.assertEqual(offer["email"], "offer2@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "0987654321")
        self.assertEqual(offer["message"], "Message2")
        self.assertEqual(offer["user"], self.test_user.id)
        self.assertEqual(offer["sublet"], self.first_sublet.id)
        self.assertIsNotNone(offer["id"])
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
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/offers/", payload)
        response = self.client.get("/sublet/offers/")
        self.assertEqual(1, len(json.loads(response.content)))
        payload = {
            "email": "offer2@seas.upenn.edu",
            "phone_number": "0987654321",
            "message": "Message2",
        }
        self.client.post(f"/sublet/properties/{str(self.second_sublet.id)}/offers/", payload)
        response = self.client.get("/sublet/offers/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json))
        offer = res_json[0]
        self.assertEqual(offer["email"], "offer@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "1234567890")
        self.assertEqual(offer["message"], "Message")
        self.assertEqual(offer["user"], self.user.id)
        self.assertEqual(offer["sublet"], self.first_sublet.id)
        self.assertIsNotNone(offer["id"])
        self.assertIsNotNone(offer["created_date"])
        offer = res_json[1]
        self.assertEqual(offer["email"], "offer2@seas.upenn.edu")
        self.assertEqual(offer["phone_number"], "0987654321")
        self.assertEqual(offer["message"], "Message2")
        self.assertEqual(offer["user"], self.user.id)
        self.assertEqual(offer["sublet"], self.second_sublet.id)
        self.assertIsNotNone(offer["id"])
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
            self.first_sublet = Sublet.objects.create(subletter=self.user, **data[0])
            self.second_sublet = Sublet.objects.create(subletter=test_user, **data[1])

    def test_create_favorite(self):
        prop_url1 = f"/sublet/properties/{str(self.first_sublet.id)}/favorites/"
        prop_url2 = f"/sublet/properties/{str(self.second_sublet.id)}/favorites/"
        self.client.post(prop_url2)
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.client.post(prop_url1)
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.assertEqual(self.client.post(prop_url1).status_code, 406)

    def test_delete_favorite(self):
        self.client.post(f"/sublet/properties/{str(self.second_sublet.id)}/favorites/")
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        self.client.delete(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.client.delete(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        self.assertTrue(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())
        self.client.delete(f"/sublet/properties/{str(self.second_sublet.id)}/favorites/")
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.second_sublet.id).exists())
        self.assertFalse(self.user.sublets_favorited.filter(pk=self.first_sublet.id).exists())

    def test_get_favorite_user(self):
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 0)
        self.client.post(f"/sublet/properties/{str(self.second_sublet.id)}/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 1)
        self.assertEqual(res_json[0]["id"], self.second_sublet.id)
        self.client.post(f"/sublet/properties/{str(self.first_sublet.id)}/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 2)
        self.client.delete(f"/sublet/properties/{str(self.second_sublet.id)}/favorites/")
        response = self.client.get("/sublet/favorites/")
        res_json = json.loads(response.content)
        self.assertEqual(len(res_json), 1)
        self.assertEqual(res_json[0]["id"], self.first_sublet.id)
