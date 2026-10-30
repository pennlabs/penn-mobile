import json

import fakeredis
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from presence import store
from presence.models import PresenceOptIn


User = get_user_model()


class PresenceStoreTestCase(TestCase):
    def setUp(self):
        store._client = fakeredis.FakeStrictRedis(decode_responses=True)


class TestTokenStore(PresenceStoreTestCase):
    def test_issued_token_is_valid_with_ttl(self):
        token = store.issue_token()
        self.assertTrue(store.is_valid_token(token))
        ttl = store._client.ttl(f"presence:token:{token}")
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, store.TOKEN_TTL_SECONDS)

    def test_unknown_token_is_invalid(self):
        self.assertFalse(store.is_valid_token("made-up"))

    def test_rotation_invalidates_previous_token(self):
        old = store.issue_token()
        new = store.issue_token(previous=old)
        self.assertNotEqual(old, new)
        self.assertTrue(store.is_valid_token(new))
        self.assertFalse(store.is_valid_token(old))
        self.assertIsNone(store.issue_token(previous=old))

    def test_issuance_counter_expires(self):
        for _ in range(store.TOKEN_ISSUE_HOURLY_LIMIT):
            self.assertTrue(store.allow_issuance(1))
        self.assertFalse(store.allow_issuance(1))
        self.assertTrue(store.allow_issuance(2))
        ttl = store._client.ttl("presence:issued:1")
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, 3600)


class TestTokenView(PresenceStoreTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.user)
        PresenceOptIn.set_for_user(self.user, True, settings.PRESENCE_PRIVACY_POLICY_VERSION)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(403, self.client.post("/presence/token/").status_code)

    def test_requires_opt_in(self):
        PresenceOptIn.set_for_user(self.user, False)
        response = self.client.post("/presence/token/")
        self.assertEqual(403, response.status_code)

    def test_issues_token(self):
        response = self.client.post("/presence/token/")
        self.assertEqual(200, response.status_code)
        res_json = json.loads(response.content)
        self.assertEqual(store.TOKEN_TTL_SECONDS, res_json["expires_in"])
        self.assertTrue(store.is_valid_token(res_json["token"]))

    def test_rotation_via_view(self):
        old = json.loads(self.client.post("/presence/token/").content)["token"]
        response = self.client.post("/presence/token/", {"previous": old}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertFalse(store.is_valid_token(old))

    def test_issuance_rate_limited_per_user(self):
        for _ in range(store.TOKEN_ISSUE_HOURLY_LIMIT):
            self.assertEqual(200, self.client.post("/presence/token/").status_code)
        self.assertEqual(429, self.client.post("/presence/token/").status_code)
        other = User.objects.create_user("other", "other@seas.upenn.edu", "other")
        PresenceOptIn.set_for_user(other, True, settings.PRESENCE_PRIVACY_POLICY_VERSION)
        self.client.force_authenticate(user=other)
        self.assertEqual(200, self.client.post("/presence/token/").status_code)
