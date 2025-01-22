import json
import pytz
import datetime
from unittest.mock import MagicMock
from django.utils.timezone import now

from django.contrib.auth import get_user_model
from django.core.files.storage import Storage
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from market.models import Offer, Item, Tag, Category, Sublet, ItemImage
from market.serializers import ItemSerializer


User = get_user_model()

# To run: python manage.py test ./tests/market
class TestMarket(TestCase):
    """Tests Create/Update/Retrieve/List for market"""

    def setUp(self):
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        user1 = User.objects.create_user("user1", "user1@seas.upenn.edu", "user1")
        user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        tags = ['New', 'Used', 'Couch', 'Laptop', 'Textbook', 'Chair', 'Apartment', 'House']
        categories = ["Book", "Electronics", "Furniture", "Food", "Sublet", "Other"]
        for tag in tags:
            Tag.objects.create(name=tag)
        for category in categories:
            Category.objects.create(name=category)
        # "backend/tests/market/mock_items.json" if debugging
        # "tests/market/mock_items.json" if from backend directory
        with open("tests/market/mock_items.json") as data:
            data = json.load(data)
            for item in data:
                created_item = Item.objects.create(
                    seller=self.user,
                    category=Category.objects.get(name=item["category"]),
                    title=item["title"],
                    description=item["description"],
                    external_link=item["external_link"],
                    price=item["price"],
                    negotiable=item["negotiable"],
                    created_at=now(),
                    expires_at=item["expires_at"]
                )
                created_item.tags.set(Tag.objects.filter(name__in=item["tags"]))
                created_item.save()
        with open("tests/market/mock_sublets.json") as data:
            data = json.load(data)
            for sublet in data:
                item = Item.objects.create(
                    seller=self.user,
                    category=Category.objects.get(name="Sublet"),
                    title=sublet["item"]["title"],
                    description=sublet["item"]["description"],
                    external_link=sublet["item"]["external_link"],
                    price=sublet["item"]["price"],
                    negotiable=sublet["item"]["negotiable"],
                    created_at=now(),
                    expires_at=sublet["item"]["expires_at"]
                )
                item.tags.set(Tag.objects.filter(name__in=sublet["tags"]))
                item.save()
                Sublet.objects.create(
                    item=item,
                    address=sublet["address"],
                    beds=sublet["beds"],
                    baths=sublet["baths"],
                    start_date=sublet["start_date"],
                    end_date=sublet["end_date"]
                )

        storage_mock = MagicMock(spec=Storage, name='StorageMock')
        storage_mock.generate_filename = lambda filename: filename
        storage_mock.save = MagicMock(side_effect=lambda name, *args, **kwargs: name)
        storage_mock.url = MagicMock(name="url")
        storage_mock.url.return_value = "http://penn-mobile.com/mock-image.png"
        ItemImage._meta.get_field("image").storage = storage_mock

    def test_create_item_all_fields(self):
        payload = {
            "id": 88,
            "seller": 2,
            "buyers": [],
            "tags": [
                "New"
            ],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "created_at": "2024-11-26T00:50:03.217587-05:00",
            "expires_at": "2025-12-12T00:00:00-05:00",
            "images": []
        }
        response = self.client.post("/market/items/", payload)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response_without_created_at = {
            "id": 5,
            "seller": 1,
            "buyers": [],
            "tags": [
                "New"
            ],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2025-12-12T00:00:00-05:00",
            "images": [],
            "favorites": []
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response_without_created_at)
        # Check that the created at time is within 1 minute of the current time.
        self.assertLessEqual(abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))), datetime.timedelta(minutes=1))

    def test_create_item_exclude_unrequired(self):
        payload = {
            "tags": [
                "New"
            ],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00"
        }
        response = self.client.post("/market/items/", payload)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response_without_created_at = {
            "id": 5,
            "seller": 1,
            "buyers": [],
            "tags": [
                "New"
            ],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": None,
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00",
            "images": [],
            "favorites": []
        }
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_without_created_at, expected_response_without_created_at)
        # Check that the created at time is within 1 minute of the current time.
        self.assertLessEqual(abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))), datetime.timedelta(minutes=1))


    def test_create_item_invalid_category(self):
        payload = {
            "tags": [
                "New"
            ],
            "category": "Textbook",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00"
        }
        response = self.client.post("/market/items/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res_json, {"category": ['Invalid pk "Textbook" - object does not exist.']})

    def test_create_item_invalid_tag(self):
        payload = {
            "tags": [
                "Not a tag"
            ],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00"
        }
        response = self.client.post("/market/items/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res_json, {"tags": ['Invalid pk "Not a tag" - object does not exist.']})

    def test_create_item_with_profanity_title(self):
        payload = {
            "tags": [
                "New"
            ],
            "category": "Book",
            "title": "Fuck Textbook",
            "description": "Fuck 2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "2024-12-12T00:00:00-05:00"
        }
        response = self.client.post("/market/items/", payload)
        self.assertEqual(response.status_code, 400)

        res_json = response.json()
        self.assertIn("title", res_json)
        self.assertIn("description", res_json)
        self.assertEqual(res_json["title"][0], "The title contains inappropriate language.")
        self.assertEqual(
            res_json["description"][0], "The description contains inappropriate language."
        )

    def test_update_item_minimum_required(self):
        # All fields included are strictly required.
        payload = {
            "category": "Book",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "2024-12-13T00:00:00-05:00"
        }
        response = self.client.patch("/market/items/1/", payload)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        expected_response = {
            "id": 1,
            "seller": 1,
            "buyers": [],
            "tags": ["Textbook", "Used"],
            "category": "Book",
            "title": "Physics Textbook",
            "description": "2023 version",
            "external_link": 'https://example.com/book',
            "price": 25.0,
            "negotiable": True,
            "expires_at": "2024-12-13T00:00:00-05:00",
            "images": [],
            "favorites": []
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_without_created_at, expected_response)
        # Check that the created at time is within 1 minute of the current time.
        self.assertLessEqual(abs(created_at - datetime.datetime.now(pytz.timezone("UTC"))), datetime.timedelta(minutes=1))


    def test_update_item_all_fields(self):
        payload = {
            "id": 5,
            "seller": 1,
            "buyers": [],
            "tags": [
                "New"
            ],
            "category": "Food",
            "title": "5 meal swipes",
            "description": "5 meal swipes for sale",
            "external_link": "https://example.com/meal-swipes",
            "price": 25.0,
            "negotiable": False,
            "created_at": "2024-11-26T00:50:03.217587-05:00",
            "expires_at": "2024-12-14T00:00:00-05:00",
            "images": []
        }
        original_item = self.client.get("/market/items/1/").json()
        original_created_at = Item.objects.get(id=1).created_at
        response = self.client.patch("/market/items/1/", payload)
        response_without_created_at = response.json().copy()
        created_at = response_without_created_at.pop("created_at")
        created_at = datetime.datetime.fromisoformat(created_at)
        self.assertEqual(response.status_code, 200)

        expected_response = {
            "id": 1,
            "seller": 1,
            "buyers": [],
            "tags": ["New"],
            "category": "Food",
            "title": "5 meal swipes",
            "description": "5 meal swipes for sale",
            "external_link": "https://example.com/meal-swipes",
            "price": 25.0,
            "negotiable": False,
            "expires_at": "2024-12-14T00:00:00-05:00",
            "images": [],
            "favorites": []
        }
        self.assertEqual(response_without_created_at, expected_response)
        # Check that the created time didn't change
        self.assertEqual(original_created_at, created_at)

    def test_update_item_invalid_category(self):
        payload = {
            "category": "Textbook",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "2024-12-13T00:00:00-05:00"
        }
        response = self.client.patch("/market/items/1/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res_json, {"category": ['Invalid pk "Textbook" - object does not exist.']})

    def test_update_item_invalid_tag(self):
        payload = {
            "tags": [
                "Not a tag"
            ],
            "category": "Book",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "2024-12-13T00:00:00-05:00"
        }
        response = self.client.patch("/market/items/1/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(res_json, {"tags": ['Invalid pk "Not a tag" - object does not exist.']})

    def test_update_item_to_sublet(self):
        payload = {
            "category": "Sublet"
        }
        response = self.client.patch("/market/items/1/", payload)
        self.assertEqual(response.status_code, 400)
        res_json = response.json()
        self.assertEqual(res_json, {"sublet": ["Sublet must not be null when category is 'Sublet'."]})

    def test_get_sublets(self):
        response = self.client.get("/market/sublets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        expected_response = {
            "id": 27,
            "item": {
                "id": 70,
                "seller": 3,
                "buyer_count": 0,
                "tags": [
                    "New"
                ],
                "category": "Sublet",
                "title": "Cira Green Sublet 2",
                "description": "Fully furnished 3-bedroom apartment available for sublet with all amenities included.",
                "price": 1350.0,
                "negotiable": false,
                "created_at": "2024-11-13T20:14:34.604238-05:00",
                "expires_at": "2025-12-12T00:00:00-05:00",
                "images": [],
                "favorites": []
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00"
        }
        self.assertEqual(response.json()[0], expected_response)