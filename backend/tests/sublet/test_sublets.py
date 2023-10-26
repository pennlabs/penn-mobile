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


def mock_sublets(*args):
    with open("tests/sublet/amenities.json") as data:
        return json.load(data)


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
        with open("tests/sublet/mock_sublets.json") as data:
            Sublet.objects.create(json.load(data)[0])
            Sublet.objects.create(json.load(data)[1])


class TestFavorites(TestCase):
    """Tests Create/Delete/List for favorites"""
    pass
