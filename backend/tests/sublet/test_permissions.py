import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from sublet.models import Amenity, Sublet


User = get_user_model()


class SubletPermissions(TestCase):
    # TODO: Include amenities in auth test when this is done
    pass


class OfferPermissions(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "admin")
        self.user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        self.user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        for i in range(1, 6):
            Amenity.objects.create(name=f"Amenity{str(i)}")
        # TODO: Add amenities
        with open("tests/sublet/mock_sublets.json") as data:
            data = json.load(data)
            self.sublet1 = Sublet.objects.create(subletter=self.admin, **data[0])
            self.sublet2 = Sublet.objects.create(subletter=self.user1, **data[0])
            self.sublet3 = Sublet.objects.create(subletter=self.user2, **data[1])

    def test_authentication(self):
        prop_url = f"/sublet/properties/{str(self.sublet1.id)}/offers/"
        self.assertEqual(self.client.get(prop_url).status_code, 403)
        self.assertEqual(self.client.post(prop_url).status_code, 403)
        self.assertEqual(self.client.delete(prop_url).status_code, 403)
        self.assertEqual(self.client.get("/sublet/offers/").status_code, 403)

    def create_create_offer(self):
        prop_url = f"/sublet/properties/{str(self.sublet1.id)}/offers/"
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        users = [self.admin, self.user1]
        for u in users:
            self.client.force_authenticate(user=u)
            self.assertEqual(self.client.post(prop_url, payload).status_code, 201)

    def test_delete_offer(self):
        prop_url = f"/sublet/properties/{str(self.sublet1.id)}/offers/"
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        users = [self.admin, self.user1]
        for u in users:
            self.client.force_authenticate(user=u)
            self.client.post(prop_url, payload)
            self.assertEqual(self.client.delete(prop_url).status_code, 204)

    def test_get_offers_property(self):
        prop_url = f"/sublet/properties/{str(self.sublet2.id)}/offers/"
        payload = {
            "email": "offer@seas.upenn.edu",
            "phone_number": "1234567890",
            "message": "Message",
        }
        users = [self.admin, self.user1, self.user2]
        codes = [200, 200, 403]
        for u in users:
            self.client.force_authenticate(user=u)
            self.client.post(prop_url, payload)
        for u, c in zip(users, codes):
            self.client.force_authenticate(user=u)
            self.assertEqual(self.client.get(prop_url).status_code, c)

    def test_get_offers_user(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self.client.get("/sublet/offers/").status_code, 200)


class FavoritePermissions(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "admin")
        self.user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        self.user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        for i in range(1, 6):
            Amenity.objects.create(name=f"Amenity{str(i)}")
        # TODO: Add amenities
        with open("tests/sublet/mock_sublets.json") as data:
            data = json.load(data)
            self.sublet1 = Sublet.objects.create(subletter=self.admin, **data[0])
            self.sublet2 = Sublet.objects.create(subletter=self.user1, **data[0])
            self.sublet3 = Sublet.objects.create(subletter=self.user2, **data[1])

    def test_authentication(self):
        prop_url = f"/sublet/properties/{str(self.sublet1.id)}/favorites/"
        self.assertEqual(self.client.post(prop_url).status_code, 403)
        self.assertEqual(self.client.delete(prop_url).status_code, 403)
        self.assertEqual(self.client.get("/sublet/favorites/").status_code, 403)

    def test_create_favorite(self):
        prop_url = f"/sublet/properties/{str(self.sublet1.id)}/favorites/"
        users = [self.admin, self.user1]
        for u in users:
            self.client.force_authenticate(user=u)
            self.assertEqual(self.client.post(prop_url).status_code, 201)

    def test_delete_favorite(self):
        prop_url = f"/sublet/properties/{str(self.sublet1.id)}/favorites/"
        users = [self.admin, self.user1]
        for u in users:
            self.client.force_authenticate(user=u)
            self.client.post(prop_url)
            self.assertEqual(self.client.delete(prop_url).status_code, 204)

    def test_get_favorites_user(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self.client.get("/sublet/favorites/").status_code, 200)
