import datetime
import json
from unittest.mock import MagicMock

import pytz
from django.contrib.auth import get_user_model
from django.core.files.storage import Storage
from django.test import TestCase
from django.utils.timezone import now
from rest_framework.test import APIClient

from market.models import Category, Item, ItemImage, Offer, Sublet, Tag


User = get_user_model()


class BaseMarketTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def load_tags(self):
        tags = [
            "New",
            "Used",
            "Couch",
            "Laptop",
            "Textbook",
            "Chair",
            "Apartment",
            "House",
        ]
        tag_objects = Tag.objects.bulk_create([Tag(name=tag) for tag in tags])

        return tag_objects

    def load_categories(self):
        categories = [
            "Book",
            "Electronics",
            "Furniture",
            "Food",
            "Sublet",
            "Other",
        ]
        category_objects = Category.objects.bulk_create([Category(name=cat) for cat in categories])
        return category_objects

    def load_user(self, username, email=None, password=None, is_self=False, auth=False):
        user = User.objects.create_user(username, email, password)
        if is_self:
            self.user = user
        if auth:
            self.client.force_authenticate(user)
        return user

    def load_items(self, filepath, user):
        items = []
        with open(filepath) as data:
            data = json.load(data)
            for item in data:
                created_item = Item.objects.create(
                    seller=user,
                    category=Category.objects.get(name=item["category"]),
                    title=item["title"],
                    description=item["description"],
                    price=item["price"],
                    negotiable=item["negotiable"],
                    created_at=now(),
                    expires_at=item["expires_at"],
                    external_link=item["external_link"],
                )
                created_item.tags.set(Tag.objects.filter(name__in=item["tags"]))
                created_item.save()
                items.append(created_item)
        return items

    def load_sublets(self, filepath, user):
        items, sublets = [], []
        with open(filepath) as data:
            data = json.load(data)
            for sublet in data:
                created_item = Item.objects.create(
                    seller=user,
                    category=Category.objects.get(name="Sublet"),
                    title=sublet["item"]["title"],
                    description=sublet["item"]["description"],
                    price=sublet["item"]["price"],
                    negotiable=sublet["item"]["negotiable"],
                    created_at=now(),
                    expires_at=sublet["item"]["expires_at"],
                    external_link=sublet["item"]["external_link"],
                )
                created_sublet = Sublet.objects.create(
                    item=created_item,
                    address=sublet["address"],
                    beds=sublet["beds"],
                    baths=sublet["baths"],
                    start_date=sublet["start_date"],
                    end_date=sublet["end_date"],
                )
                created_item.tags.set(Tag.objects.filter(name__in=sublet["item"]["tags"]))
                created_item.save()
                created_sublet.save()
                items.append(created_item)
                sublets.append(created_sublet)
        return items, sublets

    def assert_dict_equal_ignoring_keys(self, actual, expected, ignored_keys=(), unordered_keys=()):
        ignored = set(ignored_keys)
        unordered = set(unordered_keys)

        def sort_key(x):
            if isinstance(x, dict):
                return json.dumps(x, sort_keys=True)
            else:
                return str(x)

        def normalize(obj, path=""):
            if isinstance(obj, dict):
                out = {}
                for k, v in obj.items():
                    p = f"{path}{k}"
                    if p in ignored:
                        continue
                    val = normalize(v, p + ".")
                    if p in unordered and isinstance(val, list):
                        val = sorted(val, key=sort_key)
                    out[k] = val
                return out

            elif isinstance(obj, list):
                items = [normalize(e, path) for e in obj]
                if path.rstrip(".") in unordered:
                    items = sorted(items, key=sort_key)
                return items

            return obj

        self.assertEqual(normalize(actual), normalize(expected))


class TestItemGet(BaseMarketTest):
    def setUp(self):
        super().setUp()
        self.tags = self.load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]
        self.items = self.load_items(
            "tests/market/self_user_items.json", self.users[0]
        ) + self.load_items("tests/market/user_1_items.json", self.users[1])

    def test_get_items(self):
        response = self.client.get("/market/items/")
        expected_response = [
            {
                "id": self.items[0].id,
                "seller": self.users[0].id,
                "tags": ["Textbook", "Used"],
                "category": "Book",
                "title": "Math Textbook",
                "price": 20.0,
                "expires_at": "3000-12-12T00:00:00-05:00",
                "images": [],
                "favorite_count": 0,
            },
            {
                "id": self.items[1].id,
                "seller": self.users[1].id,
                "tags": ["Laptop", "New"],
                "category": "Electronics",
                "title": "Macbook Pro",
                "price": 2000.0,
                "expires_at": "3000-08-12T01:00:00-04:00",
                "images": [],
                "favorite_count": 0,
            },
            {
                "id": self.items[2].id,
                "seller": self.users[1].id,
                "tags": ["Couch"],
                "category": "Furniture",
                "title": "Couch",
                "price": 400.0,
                "expires_at": "3000-12-12T00:00:00-05:00",
                "images": [],
                "favorite_count": 0,
            },
        ]
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(), expected_response, [], ["", "tags", "images"]
        )

    def test_get_item_seller(self):
        response = self.client.get("/market/items/?seller=true")
        expected_response = [
            {
                "id": self.items[0].id,
                "seller": self.users[0].id,
                "tags": ["Textbook", "Used"],
                "category": "Book",
                "title": "Math Textbook",
                "price": 20.0,
                "expires_at": "3000-12-12T00:00:00-05:00",
                "images": [],
                "favorite_count": 0,
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(), expected_response, [], ["", "tags", "images"]
        )

    def test_get_single_item_own(self):
        response = self.client.get(f"/market/items/{self.items[0].id}/")
        response_json = response.json()
        expected_response = {
            "id": self.items[0].id,
            "images": [],
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/book",
            "price": 20.0,
            "negotiable": True,
            "created_at": "2025-09-04T14:01:34.530659-04:00",
            "expires_at": "3000-12-12T00:00:00-05:00",
            "seller": self.users[0].id,
            "category": "Book",
            "buyers": [],
            "tags": ["Textbook", "Used"],
            "favorites": [],
        }
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response_json,
            expected_response,
            ["created_at"],
            ["", "tags", "images", "buyers", "favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response_json["created_at"])
                - datetime.datetime.now(pytz.UTC)
            ),
            datetime.timedelta(minutes=10),
        )

    def test_get_single_item_other(self):
        response = self.client.get(f"/market/items/{self.items[1].id}/")
        expected_response = {
            "id": self.items[1].id,
            "seller": self.users[1].id,
            "buyer_count": 0,
            "tags": ["Laptop", "New"],
            "category": "Electronics",
            "title": "Macbook Pro",
            "description": "M1 Chip",
            "external_link": "https://example.com/macbook",
            "price": 2000.0,
            "negotiable": True,
            "expires_at": "3000-08-12T01:00:00-04:00",
            "images": [],
            "favorite_count": 0,
        }
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(), expected_response, [], ["", "tags", "images"]
        )


class TestItemPost(BaseMarketTest):

    def setUp(self):
        super().setUp()
        self.tags = self.load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]

    def test_create_item_all_fields(self):
        payload = {
            "id": 88,
            "seller": self.users[1].id,
            "buyers": [],
            "tags": ["New"],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "created_at": "2024-11-26T00:50:03.217587-05:00",
            "expires_at": "3000-12-12T00:00:00-05:00",
            "images": [],
        }
        response = self.client.post("/market/items/", payload, format="json")
        expected_response = {
            "id": int(f"{response.json()['id']}"),
            "images": [],
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "created_at": "2025-09-04T15:00:58.895709-04:00",
            "expires_at": "3000-12-12T00:00:00-05:00",
            "seller": self.users[0].id,
            "category": "Book",
            "buyers": [],
            "tags": ["New"],
            "favorites": [],
        }
        self.assertEqual(response.status_code, 201)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["", "tags", "images", "buyers", "favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.UTC)
            ),
            datetime.timedelta(minutes=10),
        )
        response = self.client.get(f"/market/items/{response.json()['id']}/")
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["", "tags", "images", "buyers", "favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )

    def test_create_item_exclude_unrequired(self):
        payload = {
            "tags": ["New"],
            "category": "Book",
            "title": "Math Textbook",
            "description": "2023 version",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "3000-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload, format="json")
        expected_response = {
            "id": int(f"{response.json()['id']}"),
            "images": [],
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": None,
            "price": 20.0,
            "negotiable": True,
            "created_at": "2025-09-04T15:00:58.895709-04:00",
            "expires_at": "3000-12-12T00:00:00-05:00",
            "seller": self.users[0].id,
            "category": "Book",
            "buyers": [],
            "tags": ["New"],
            "favorites": [],
        }
        self.assertEqual(response.status_code, 201)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["", "tags", "images", "buyers", "favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.UTC)
            ),
            datetime.timedelta(minutes=10),
        )
        response = self.client.get(f"/market/items/{response.json()['id']}/")
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["", "tags", "images", "buyers", "favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )

    def test_create_item_missing_field(self):
        payload = {
            "tags": ["New"],
            "category": "Book",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "3000-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"title": ["This field is required."]})

    def test_create_item_invalid_category(self):
        payload = {
            "tags": ["New"],
            "category": "Textbook",
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "3000-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            res_json,
            {"category": ['Invalid pk "Textbook" - object does not exist.']},
        )

    def test_create_item_with_profanity_title(self):
        payload = {
            "tags": ["New"],
            "category": "Book",
            "title": "Fuck Textbook",
            "description": "Fuck 2023 version",
            "external_link": "https://example.com/listing",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "3000-12-12T00:00:00-05:00",
        }
        response = self.client.post("/market/items/", payload)
        self.assertEqual(response.status_code, 400)

        res_json = response.json()
        self.assertIn("title", res_json)
        self.assertIn("description", res_json)
        self.assertEqual(res_json["title"][0], "The title contains inappropriate language.")
        self.assertEqual(
            res_json["description"][0],
            "The description contains inappropriate language.",
        )


class TestItemPatch(BaseMarketTest):
    def setUp(self):
        super().setUp()
        self.tags = self.load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]
        self.items = self.load_items(
            "tests/market/self_user_items.json", self.users[0]
        ) + self.load_items("tests/market/user_1_items.json", self.users[1])

    def test_update_item_minimum_required(self):
        payload = {
            "category": "Book",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "3000-12-13T00:00:00-05:00",
        }
        response = self.client.patch(f"/market/items/{self.items[0].id}/", payload)
        expected_response = {
            "id": self.items[0].id,
            "seller": self.users[0].id,
            "buyers": [],
            "tags": ["Used", "Textbook"],
            "category": "Book",
            "title": "Physics Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/book",
            "price": 25.0,
            "negotiable": True,
            "expires_at": "3000-12-13T00:00:00-05:00",
            "images": [],
            "favorites": [],
        }
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["tags", "images", "favorites", "buyers"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )
        response = self.client.get(f"/market/items/{self.items[0].id}/")
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["tags", "images", "favorites", "buyers"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )

    def test_update_item_all_fields(self):
        payload = {
            "id": 7,
            "seller": self.users[1].id,
            "buyers": [],
            "tags": ["New"],
            "category": "Food",
            "title": "5 meal swipes",
            "description": "5 meal swipes for sale",
            "external_link": "https://example.com/meal-swipes",
            "price": 25.0,
            "negotiable": False,
            "created_at": "2024-11-26T00:50:03.217587-05:00",
            "expires_at": "3000-12-14T00:00:00-05:00",
            "images": [],
        }
        response = self.client.patch(f"/market/items/{self.items[0].id}/", payload)
        expected_response = {
            "id": self.items[0].id,
            "seller": self.users[0].id,
            "buyers": [],
            "tags": ["New"],
            "category": "Food",
            "title": "5 meal swipes",
            "description": "5 meal swipes for sale",
            "external_link": "https://example.com/meal-swipes",
            "price": 25.0,
            "negotiable": False,
            "expires_at": "3000-12-14T00:00:00-05:00",
            "images": [],
            "favorites": [],
        }

        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["tags", "images", "buyers", "favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )
        response = self.client.get(f"/market/items/{self.items[0].id}/")
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["tags", "images", "buyers", "favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )

    def test_update_item_invalid_category(self):
        payload = {
            "category": "Textbook",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "3000-12-13T00:00:00-05:00",
        }
        response = self.client.patch(f"/market/items/{self.items[0].id}/", payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"category": ['Invalid pk "Textbook" - object does not exist.']},
        )

    def test_update_item_invalid_tag(self):
        payload = {
            "tags": ["Not a tag"],
            "category": "Book",
            "title": "Physics Textbook",
            "price": 25.0,
            "expires_at": "3000-12-13T00:00:00-05:00",
        }
        response = self.client.patch(f"/market/items/{self.items[0].id}/", payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"tags": ['Invalid pk "Not a tag" - object does not exist.']},
        )

    def test_update_item_to_sublet(self):
        response = self.client.patch(f"/market/items/{self.items[0].id}/", {"category": "Sublet"})
        expected_response = {
            "id": self.items[0].id,
            "images": [],
            "title": "Math Textbook",
            "description": "2023 version",
            "external_link": "https://example.com/book",
            "price": 20.0,
            "negotiable": True,
            "expires_at": "3000-12-12T00:00:00-05:00",
            "seller": self.users[0].id,
            "category": "Sublet",
            "buyers": [],
            "tags": ["Textbook", "Used"],
            "favorites": [],
        }
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["tags", "images", "buyers", "favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )

    def test_update_item_not_owned(self):
        payload = {"title": "New Title"}
        response = self.client.patch(f"/market/items/{self.items[1].id}/", payload, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"detail": "You do not have permission to perform this action."},
        )


class TestItemDelete(BaseMarketTest):
    def setUp(self):
        super().setUp()
        self.tags = self.load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]
        self.items = self.load_items(
            "tests/market/self_user_items.json", self.users[0]
        ) + self.load_items("tests/market/user_1_items.json", self.users[1])

    def test_delete_item(self):
        self.assertTrue(Item.objects.filter(id=self.items[0].id).exists())
        response = self.client.delete(f"/market/items/{self.items[0].id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Item.objects.filter(id=self.items[0].id).exists())

    def test_delete_item_not_owned(self):
        response = self.client.delete(f"/market/items/{self.items[1].id}/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {"detail": "You do not have permission to perform this action."},
        )


class TestSubletGet(BaseMarketTest):
    def setUp(self):
        super().setUp()
        self.tags = self.load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]
        items1, sublets1 = self.load_sublets("tests/market/self_user_sublets.json", self.users[0])
        items2, sublets2 = self.load_sublets("tests/market/user_1_sublets.json", self.users[1])
        self.items = items1 + items2
        self.sublets = sublets1 + sublets2

    def test_get_sublets(self):
        response = self.client.get("/market/sublets/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        expected_response = [
            {
                "id": self.sublets[0].id,
                "item": {
                    "id": self.items[0].id,
                    "seller": self.users[0].id,
                    "tags": ["New"],
                    "category": "Sublet",
                    "title": "Cira Green Sublet",
                    "price": 1350.0,
                    "expires_at": "3000-12-12T00:00:00-05:00",
                    "images": [],
                    "favorite_count": 0,
                },
                "address": "Cira Green, Philadelphia, PA",
                "beds": 3.0,
                "baths": 1.0,
                "start_date": "2024-01-01T00:00:00-05:00",
                "end_date": "3000-05-31T00:00:00-04:00",
            },
            {
                "id": self.sublets[1].id,
                "item": {
                    "id": self.items[1].id,
                    "seller": self.users[1].id,
                    "tags": ["New"],
                    "category": "Sublet",
                    "title": "Rodin Quad",
                    "price": 1350.0,
                    "expires_at": "3000-12-12T00:00:00-05:00",
                    "images": [],
                    "favorite_count": 0,
                },
                "address": "3901 Locust Walk, Philadelphia, PA",
                "beds": 4.0,
                "baths": 1.0,
                "start_date": "2024-01-01T00:00:00-05:00",
                "end_date": "3000-05-31T00:00:00-04:00",
            },
        ]
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["created_at"],
            ["", "tags", "images", "buyers", "favorites"],
        )

    def test_get_sublet_own(self):
        response = self.client.get(f"/market/sublets/{self.sublets[0].id}/")
        self.assertEqual(response.status_code, 200)
        expected_response = {
            "id": self.sublets[0].id,
            "item": {
                "id": self.items[0].id,
                "images": [],
                "title": "Cira Green Sublet",
                "description": "Fully furnished 3-bedroom apartment available for sublet with all"
                + " amenities included.",
                "external_link": "https://example.com/cira-green",
                "price": 1350.0,
                "negotiable": False,
                "created_at": "2025-09-05T00:14:15.141807-04:00",
                "expires_at": "3000-12-12T00:00:00-05:00",
                "seller": self.users[0].id,
                "category": "Sublet",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "Cira Green, Philadelphia, PA",
            "beds": 3.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "3000-05-31T00:00:00-04:00",
        }
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["item.created_at"],
            ["", "item.tags", "item.images", "item.buyers", "item.favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["item"]["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )

    def test_get_sublet_other(self):
        response = self.client.get(f"/market/sublets/{self.sublets[1].id}/")
        self.assertEqual(response.status_code, 200)
        expected_response = {
            "id": self.sublets[1].id,
            "item": {
                "id": self.items[1].id,
                "seller": self.users[1].id,
                "buyer_count": 0,
                "tags": ["New"],
                "category": "Sublet",
                "title": "Rodin Quad",
                "description": "Fully furnished 4-bedroom apartment available for sublet with all"
                + " amenities included.",
                "external_link": "https://example.com/rodin-quad",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "3000-12-12T00:00:00-05:00",
                "images": [],
                "favorite_count": 0,
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "3000-05-31T00:00:00-04:00",
        }
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["item.created_at"],
            ["", "item.tags", "item.images", "item.buyers", "item.favorites"],
        )

    def test_get_single_sublet_invalid_id(self):
        response = self.client.get(f"/market/sublets/{self.sublets[1].id+1}/")
        self.assertEqual(response.status_code, 404)


class TestSubletPost(BaseMarketTest):
    def setUp(self):
        super().setUp()
        self.tags = self.load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]

    def test_create_sublet(self):
        payload = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment available"
                    " for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": self.users[0].id,
                "category": "Sublet",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "3000-05-31T00:00:00-04:00",
        }
        response = self.client.post("/market/sublets/", payload, format="json")
        expected_response = {
            "id": response.json()["id"],
            "item": {
                "id": response.json()["item"]["id"],
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": "Fully furnished 3-bedroom apartment available for sublet with all"
                + " amenities included.",
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "created_at": "2025-09-05T00:48:08.880144-04:00",
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": self.users[0].id,
                "category": "Sublet",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "3000-05-31T00:00:00-04:00",
        }
        self.assertEqual(response.status_code, 201)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["item.created_at"],
            ["item.tags", "item.images", "item.buyers", "item.favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["item"]["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )
        response = self.client.get(f"/market/sublets/{response.json()['id']}/")
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["item.created_at"],
            ["item.tags", "item.images", "item.buyers", "item.favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["item"]["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )


class TestSubletPatchDelete(BaseMarketTest):
    def setUp(self):
        super().setUp()
        self.tags = self.load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]
        items1, sublets1 = self.load_sublets("tests/market/self_user_sublets.json", self.users[0])
        items2, sublets2 = self.load_sublets("tests/market/user_1_sublets.json", self.users[1])
        self.items = items1 + items2
        self.sublets = sublets1 + sublets2

    def test_update_sublet(self):
        payload = {
            "id": 3,
            "item": {
                "id": 7,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": self.users[0].id,
                "category": "Sublet",
                "buyers": [],
                "tags": ["Apartment", "New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        response = self.client.patch(
            f"/market/sublets/{self.sublets[0].id}/", payload, format="json"
        )
        expected_response = {
            "id": int(self.sublets[0].id),
            "item": {
                "id": int(self.items[0].id),
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": self.users[0].id,
                "category": "Sublet",
                "buyers": [],
                "tags": ["New", "Apartment"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["item.created_at"],
            ["item.tags", "item.images", "item.buyers", "item.favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["item"]["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )
        response = self.client.get(f"/market/sublets/{self.sublets[0].id}/")
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["item.created_at"],
            ["item.tags", "item.images", "item.buyers", "item.favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["item"]["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )

    def test_update_sublet_non_sublet_category(self):
        payload = {
            "item": {
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": self.users[0].id,
                "category": "Book",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        response = self.client.patch(
            f"/market/sublets/{self.sublets[0].id}/", payload, format="json"
        )
        expected_response = {
            "id": self.sublets[0].id,
            "item": {
                "id": self.items[0].id,
                "images": [],
                "title": "Cira Green Sublet 2",
                "description": (
                    "Fully furnished 3-bedroom apartment "
                    "available for sublet with all amenities included."
                ),
                "external_link": "https://example.com/listing",
                "price": 1350.0,
                "negotiable": False,
                "expires_at": "2025-12-12T00:00:00-05:00",
                "seller": self.users[0].id,
                "category": "Book",
                "buyers": [],
                "tags": ["New"],
                "favorites": [],
            },
            "address": "3901 Locust Walk, Philadelphia, PA",
            "beds": 4.0,
            "baths": 1.0,
            "start_date": "2024-01-01T00:00:00-05:00",
            "end_date": "2025-05-31T00:00:00-04:00",
        }
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(),
            expected_response,
            ["item.created_at"],
            ["item.tags", "item.images", "item.buyers", "item.favorites"],
        )
        self.assertLessEqual(
            abs(
                datetime.datetime.fromisoformat(response.json()["item"]["created_at"])
                - datetime.datetime.now(pytz.timezone("UTC"))
            ),
            datetime.timedelta(minutes=10),
        )


class TestOffer(BaseMarketTest):
    def setUp(self):
        super().setUp()
        self.tags = super().load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]
        self.items = self.load_items(
            "tests/market/self_user_items.json", self.users[0]
        ) + self.load_items("tests/market/user_1_items.json", self.users[1])
        items1, sublets1 = self.load_sublets("tests/market/self_user_sublets.json", self.users[0])
        items2, sublets2 = self.load_sublets("tests/market/user_1_sublets.json", self.users[1])
        self.items += items1 + items2
        self.sublets = sublets1 + sublets2
        self.offers = [
            Offer.objects.create(
                user=self.users[0],
                item=self.items[1],
                email="self_user@gmail.com",
            ),
            Offer.objects.create(
                user=self.users[0],
                item=self.items[4],
                email="self_user@gmail.com",
                phone_number="+15555555555",
                message="I want this",
            ),
            Offer.objects.create(
                user=self.users[1],
                item=self.items[0],
                email="user1@gmail.com",
                phone_number="+15555555555",
                message="",
            ),
        ]

    def test_get_all_user_offers(self):
        response = self.client.get("/market/offers/made/")
        expected_response = [
            {
                "id": self.offers[0].id,
                "phone_number": None,
                "email": "self_user@gmail.com",
                "message": "",
                "user": self.users[0].id,
                "item": self.items[1].id,
            },
            {
                "id": self.offers[1].id,
                "phone_number": "+15555555555",
                "email": "self_user@gmail.com",
                "message": "I want this",
                "user": self.users[0].id,
                "item": self.items[4].id,
            },
        ]
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(
            response.json(), expected_response, ["created_at"], [""]
        )

    def test_list_item_offers(self):
        response = self.client.get(f"/market/items/{self.items[0].id}/offers/")
        expected = [
            {
                "id": self.offers[2].id,
                "phone_number": "+15555555555",
                "email": "user1@gmail.com",
                "message": "",
                "user": self.users[1].id,
                "item": self.items[0].id,
            }
        ]
        self.assertEqual(response.status_code, 200)
        self.assert_dict_equal_ignoring_keys(response.json(), expected, ["created_at"], [""])

    def test_get_offer_other(self):
        response = self.client.get(f"/market/items/{self.items[1].id}/offers/")
        expected = {"detail": "You do not have permission to perform this action."}
        self.assertEqual(response.status_code, 403)
        self.assert_dict_equal_ignoring_keys(response.json(), expected, ["created_at"], [""])

    def test_list_item_offers_invalid_item(self):
        invalid_id = 1
        while Item.objects.filter(id=invalid_id).exists():
            invalid_id += 1
        response = self.client.get(f"/market/items/{invalid_id}/offers/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "No Item matches the given query"})

    def test_create_offer_all_fields(self):
        payload = {
            "phone_number": "+1 (202) 555 0100",
            "email": "self_user@gmail.com",
            "message": "I want this",
        }
        response = self.client.post(
            f"/market/items/{self.items[2].id}/offers/", payload, format="json"
        )
        expected_response = {
            "id": response.json()["id"],
            "phone_number": "+12025550100",
            "email": "self_user@gmail.com",
            "message": "I want this",
            "user": self.users[0].id,
            "item": self.items[2].id,
        }
        self.assertEqual(response.status_code, 201)
        self.assert_dict_equal_ignoring_keys(
            response.json(), expected_response, ["created_at"], [""]
        )

    def test_create_offer_required_fields(self):
        payload = {"phone_number": "+12025550100"}
        response = self.client.post(
            f"/market/items/{self.items[2].id}/offers/", payload, format="json"
        )
        expected_response = {
            "id": response.json()["id"],
            "phone_number": "+12025550100",
            "email": None,
            "message": "",
            "user": self.users[0].id,
            "item": self.items[2].id,
        }
        self.assertEqual(response.status_code, 201)
        self.assert_dict_equal_ignoring_keys(
            response.json(), expected_response, ["created_at"], [""]
        )

    def test_create_offer_invalid(self):
        payload = {}
        response = self.client.post(
            f"/market/items/{self.items[2].id}/offers/", payload, format="json"
        )
        expected_response = {"phone_number": ["This field is required."]}
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), expected_response)

    def test_create_offer_existing(self):
        payload = {
            "phone_number": "+1 (202) 555 0100",
            "email": "self_user@gmail.com",
            "message": "I want this",
        }
        response = self.client.post(
            f"/market/items/{self.items[1].id}/offers/", payload, format="json"
        )
        expected_response = ["Offer already exists"]
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), expected_response)

    def test_delete_offer(self):
        self.assertTrue(Offer.objects.filter(id=self.offers[0].id).exists())
        response = self.client.delete(f"/market/items/{self.items[1].id}/offers/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Offer.objects.filter(id=self.offers[0].id).exists())

    def test_delete_offer_nonexistent(self):
        invalid_id = 1
        while Offer.objects.filter(id=invalid_id).exists():
            invalid_id += 1
        response = self.client.delete(f"/market/items/{invalid_id}/offers/")
        self.assertEqual(response.status_code, 404)


class TestImages(BaseMarketTest):
    def setUp(self):
        super().setUp()
        self.tags = self.load_tags()
        self.categories = self.load_categories()
        self.users = [
            self.load_user("user", "user@gmail.com", "user", True, True),
            self.load_user("user1", "user1@gmail.com", "user1", False, False),
        ]
        self.items = self.load_items(
            "tests/market/self_user_items.json", self.users[0]
        ) + self.load_items("tests/market/user_1_items.json", self.users[1])

        storage_mock = MagicMock(spec=Storage, name="StorageMock")
        storage_mock.generate_filename = lambda filename: filename
        storage_mock.save = MagicMock(side_effect=lambda name, *args, **kwargs: name)
        storage_mock.url = MagicMock(name="url")
        storage_mock.url.return_value = "http://penn-mobile.com/mock-image.png"
        ItemImage._meta.get_field("image").storage = storage_mock

    def test_create_image(self):
        with open("tests/market/mock_image.jpg", "rb") as image:
            self.assertEqual(Item.objects.get(id=self.items[0].id).images.count(), 0)
            response = self.client.post(
                f"/market/items/{self.items[0].id}/images/", {"images": image}
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(Item.objects.get(id=self.items[0].id).images.count(), 1)
            img = Item.objects.get(id=self.items[0].id).images.first()
            self.assertIsNotNone(img)

    def test_create_image_other_users_item(self):
        with open("tests/market/mock_image.jpg", "rb") as image:
            response = self.client.post(
                f"/market/items/{self.items[1].id}/images/", {"images": image}
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                response.json(),
                {"detail": "You do not have permission to perform this action."},
            )

    def test_create_delete_images(self):
        with open("tests/market/mock_image.jpg", "rb") as image:
            with open("tests/market/mock_image.jpg", "rb") as image2:
                response = self.client.post(
                    f"/market/items/{self.items[0].id}/images/",
                    {"images": [image, image2]},
                    "multipart",
                )
                saved_images = response.json()
                self.assertEqual(response.status_code, 201)
                images = Item.objects.get(id=self.items[0].id).images.all()
                self.assertTrue(images.exists())
                self.assertEqual(2, images.count())
                self.assertEqual(self.items[0].id, images.first().item.id)
                response = self.client.delete(f"/market/items/images/{saved_images[0]['id']}/")
                self.assertEqual(response.status_code, 204)
                self.assertFalse(ItemImage.objects.filter(id=saved_images[0]["id"]).exists())
                self.assertTrue(ItemImage.objects.filter(id=saved_images[1]["id"]).exists())
                self.assertEqual(1, ItemImage.objects.all().count())
