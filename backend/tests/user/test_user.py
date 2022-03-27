from unittest import mock

from django.contrib import auth
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from user.models import Profile


def check_wharton(*args):
    return False


User = get_user_model()


class UserTestCase(TestCase):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def setUp(self):
        self.user1 = {
            "pennid": 1,
            "first_name": "First",
            "last_name": "Last",
            "username": "user",
            "email": "test@test.com",
            "affiliation": [],
            "user_permissions": [],
            "groups": ["student", "member"],
            "token": {"access_token": "abc", "refresh_token": "123", "expires_in": 100},
        }

        self.user2 = {
            "pennid": 2,
            "first_name": "First",
            "last_name": "Last",
            "username": "user",
            "email": "test@test.com",
            "affiliation": [],
            "user_permissions": [],
            "groups": ["student", "member"],
            "token": {"access_token": "abc", "refresh_token": "123", "expires_in": 100},
        }

        self.client = APIClient()
        self.client.login(username="user1", password="password")

    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def test_user1_profile(self):
        user = auth.authenticate(remote_user=self.user1)
        self.assertEqual(1, Profile.objects.all().count())
        self.assertEqual(user, Profile.objects.all().first().user)

    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def test_user2_profile(self):
        self.assertEqual(0, Profile.objects.all().count())
        user = auth.authenticate(remote_user=self.user2)
        self.assertEqual(1, Profile.objects.all().count())
        self.assertEqual(user, Profile.objects.all().first().user)
        user.name = "New Name"
        user.save()
        self.assertEqual(1, Profile.objects.all().count())
        self.assertEqual(user, Profile.objects.all().first().user)
