import json
from unittest.mock import MagicMock
from django.utils.timezone import now

from django.contrib.auth import get_user_model
from django.core.files.storage import Storage
from django.test import TestCase
from rest_framework.test import APIClient

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
            "expires_at": "2024-12-12T00:00:00-05:00",
            "images": []
        }
        response = self.client.post("/market/items/", payload)
        res_json = json.loads(response.content)
        match_keys = ["id", "seller", "buyers", "tags", "category", "title", "description", "external_link", "price", "negotiable", "created_at", "expires_at", "images"]
        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload.keys(), res_json.keys())
        self.assertEqual(payload.keys(), set(match_keys))
        self.assertEqual(res_json["id"], 5)
        self.assertEqual(self.user.id, res_json["seller"])
        # Not sure how to check if created_at exactly matches the
        # time of the request, so just check if it's present.
        self.assertIn("created_at", res_json)
        match_keys.remove("id")
        match_keys.remove("seller")
        match_keys.remove("created_at")
        [self.assertEqual(payload[key], res_json[key]) for key in match_keys]

    def test_create_item_exclude_unrequired(self):
        payload = {
            "tags": [
                "New"
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
        match_keys = ["id", "seller", "buyers", "tags", "category", "title", "description", "external_link", "price", "negotiable", "created_at", "expires_at", "images"]
        self.assertEqual(response.status_code, 201)
        self.assertEqual(list(res_json.keys()), match_keys)
        self.assertEqual(res_json["id"], 5)
        self.assertEqual(self.user.id, res_json["seller"])
        self.assertEqual([], res_json["buyers"])
        self.assertEqual([], res_json["images"])
        # Not sure how to check if created_at exactly matches the
        # time of the request, so just check if it's present.
        self.assertIn("created_at", res_json)
        match_keys.remove("id")
        match_keys.remove("seller")
        match_keys.remove("created_at")
        match_keys.remove("buyers")
        match_keys.remove("images")
        [self.assertEqual(payload[key], res_json[key]) for key in match_keys]

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

    def test_update_item_post_minimum_required(self):
        # All fields included are strictly required.
        payload = {
            "category": "Book",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "2024-12-13T00:00:00-05:00"
        }
        response = self.client.patch("/market/items/1/", payload)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertEqual(res_json["id"], 1)
        self.assertEqual(res_json["seller"], self.user.id)
        self.assertEqual(res_json["category"], "Book")
        self.assertEqual(res_json["title"], "Physics Textbook")
        self.assertEqual(res_json["price"], 25.0)
        self.assertEqual(res_json["expires_at"], "2024-12-13T00:00:00-05:00")
        self.assertEqual(res_json["negotiable"], True)
        self.assertEqual(res_json["external_link"], "https://example.com/book")
        self.assertEqual(set(res_json["tags"]), set(["Used", "Textbook"]))
        self.assertEqual(res_json["description"], "2023 version")

    def test_update_item_post_all_fields(self):
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
        original_created_at = Item.objects.get(id=1).created_at.astimezone().isoformat()
        response = self.client.patch("/market/items/1/", payload)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertEqual(res_json["id"], original_item["id"])
        self.assertEqual(res_json["seller"], original_item["seller"])
        self.assertEqual(res_json["category"], "Food")
        self.assertEqual(set(res_json["tags"]), set(["New"]))
        self.assertEqual(res_json["title"], "5 meal swipes")
        self.assertEqual(res_json["description"], "5 meal swipes for sale")
        self.assertEqual(res_json["external_link"], "https://example.com/meal-swipes")
        self.assertEqual(res_json["price"], 25.0)
        self.assertEqual(res_json["negotiable"], False)
        # created_at needs to be retrieved seperately since it's not returned by the read-only serializer.
        self.assertEqual(res_json["created_at"], original_created_at)
        self.assertEqual(res_json["expires_at"], "2024-12-14T00:00:00-05:00")
        self.assertEqual(res_json["images"], [])