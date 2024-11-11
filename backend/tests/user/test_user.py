from django.contrib import auth
from django.test import TestCase
from rest_framework.test import APIClient

from user.models import Profile


class UserTestCase(TestCase):
    def setUp(self) -> None:
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

        self.client: APIClient = APIClient()
        self.client.login(username="user1", password="password")

    def test_user1_profile(self) -> None:
        user = auth.authenticate(remote_user=self.user1)
        self.assertEqual(1, Profile.objects.all().count())
        profile = Profile.objects.all().first()
        assert profile is not None
        self.assertEqual(user, profile.user)
        self.assertEqual("user", str(profile))

    def test_user2_profile(self) -> None:
        self.assertEqual(0, Profile.objects.all().count())
        user = auth.authenticate(remote_user=self.user2)
        assert user is not None
        self.assertEqual(1, Profile.objects.all().count())
        profile = Profile.objects.all().first()
        assert profile is not None
        self.assertEqual(user, profile.user)
        user.name = "New Name"  # type: ignore
        user.save()
        self.assertEqual(1, Profile.objects.all().count())
        profile = Profile.objects.all().first()
        assert profile is not None
        self.assertEqual(user, profile.user)
