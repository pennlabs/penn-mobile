import base64
import time
from unittest.mock import patch

import fakeredis
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from presence import blind, store
from presence.models import PresenceOptIn
from tests.presence.blind_client import BlindedToken


User = get_user_model()
HOUR = blind.KEY_EPOCH_SECONDS


def signed_token():
    """Run the whole client flow against the server functions; returns heartbeat fields."""
    key = blind.key_info()
    request = BlindedToken(key["public_key"])
    blind_signature = blind.blind_sign(key["key_id"], base64.b64decode(request.blinded_message))
    return {
        "token": request.token,
        "key_id": key["key_id"],
        "signature": request.finalize(base64.b64encode(blind_signature).decode()),
    }


def verifies(public_key_pem, token, signature):
    """Check a signature with the cryptography library, independent of presence.blind."""
    try:
        load_pem_public_key(public_key_pem.encode()).verify(
            base64.b64decode(signature),
            token.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA384()), salt_length=48),
            hashes.SHA384(),
        )
    except InvalidSignature:
        return False
    return True


class PresenceStoreTestCase(TestCase):
    def setUp(self):
        store._client = fakeredis.FakeStrictRedis(decode_responses=True)


class TestBlindSigning(PresenceStoreTestCase):
    def test_finalized_signature_verifies_for_the_token_only(self):
        fields = signed_token()
        self.assertTrue(blind.verify(**fields))
        self.assertFalse(blind.verify(**{**fields, "token": "someone-elses-token"}))
        self.assertTrue(
            verifies(blind.key_info()["public_key"], fields["token"], fields["signature"])
        )

    def test_server_only_sees_the_blinded_message(self):
        key = blind.key_info()
        first, second = (BlindedToken(key["public_key"], token="same-token") for _ in range(2))
        self.assertNotEqual(first.blinded_message, second.blinded_message)
        self.assertNotIn(b"same-token", base64.b64decode(first.blinded_message))

    def test_garbage_signature_rejected(self):
        fields = signed_token()
        for signature in ("", "not base64!", base64.b64encode(b"\x01" * 256).decode()):
            with self.subTest(signature=signature):
                self.assertFalse(blind.verify(**{**fields, "signature": signature}))
        self.assertFalse(blind.verify(**{**fields, "key_id": "not-a-key"}))

    def test_malformed_blinded_message_rejected(self):
        key_id = blind.key_info()["key_id"]
        for message in (b"", b"\x00" * 256, b"\xff" * 256, b"\x01" * 255):
            with self.subTest(message=message[:4]):
                with self.assertRaises(ValueError):
                    blind.blind_sign(key_id, message)

    def test_key_is_shared_through_redis_and_stable_within_the_hour(self):
        blind._cache.clear()  # start like a fresh process on this test's empty Redis
        first = blind.key_info()
        blind._cache.clear()  # a second web worker has no in-process copy
        self.assertEqual(first["public_key"], blind.key_info()["public_key"])
        stored = store.client().get(f"presence:signing-key:{first['key_id']}")
        self.assertIn("ENCRYPTED PRIVATE KEY", stored)  # never kept in Redis in the clear

    def test_key_rotates_hourly_and_old_tokens_expire(self):
        now = time.time()
        fields = signed_token()
        with patch("presence.blind.time.time", return_value=now + HOUR):
            self.assertNotEqual(fields["key_id"], blind.key_info()["key_id"])
            self.assertTrue(blind.verify(**fields))  # previous hour's key is still accepted
            with self.assertRaises(blind.StaleKey):
                blind.blind_sign(fields["key_id"], b"\x01" * 256)  # but no longer signs
        with patch("presence.blind.time.time", return_value=now + 2 * HOUR):
            self.assertFalse(blind.verify(**fields))

    def test_issuance_counter_expires(self):
        for _ in range(store.TOKEN_ISSUE_HOURLY_LIMIT):
            self.assertTrue(store.allow_issuance(1))
        self.assertFalse(store.allow_issuance(1))
        self.assertTrue(store.allow_issuance(2))
        ttl = store._client.ttl("presence:issued:1")
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, 3600)


class TestTokenKeyView(PresenceStoreTestCase):
    def test_public_key_is_available_without_login(self):
        response = APIClient().get("/presence/token-key/")
        self.assertEqual(200, response.status_code)
        self.assertEqual("RSABSSA-SHA384-PSS-Deterministic", response.data["algorithm"])
        self.assertEqual(2048, load_pem_public_key(response.data["public_key"].encode()).key_size)
        self.assertEqual(blind.current_key_id(), response.data["key_id"])
        self.assertTrue(0 < response.data["issues_for"] <= HOUR)
        self.assertTrue(HOUR < response.data["token_expires_in"] <= 2 * HOUR)


class TestTokenView(PresenceStoreTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.user)
        PresenceOptIn.set_for_user(self.user, True, settings.PRESENCE_PRIVACY_POLICY_VERSION)
        self.key = self.client.get("/presence/token-key/").data

    def request_signature(self, **overrides):
        self.blinded = BlindedToken(self.key["public_key"])
        body = {"key_id": self.key["key_id"], "blinded_message": self.blinded.blinded_message}
        return self.client.post("/presence/token/", {**body, **overrides}, format="json")

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(403, self.request_signature().status_code)

    def test_requires_opt_in(self):
        PresenceOptIn.set_for_user(self.user, False)
        self.assertEqual(403, self.request_signature().status_code)

    def test_signs_a_token_the_server_never_sees(self):
        response = self.request_signature()
        self.assertEqual(200, response.status_code)
        self.assertEqual({"key_id", "blind_signature", "expires_in"}, set(response.data))
        self.assertTrue(HOUR < response.data["expires_in"] <= 2 * HOUR)
        signature = self.blinded.finalize(response.data["blind_signature"])
        self.assertTrue(verifies(self.key["public_key"], self.blinded.token, signature))
        # Nothing about the token is stored at issuance.
        self.assertEqual([], store.client().keys("presence:token:*"))

    def test_malformed_request(self):
        for overrides in (
            {"blinded_message": "not base64!"},
            {"blinded_message": base64.b64encode(b"\x01" * 10).decode()},
            {"blinded_message": ""},
            {"key_id": ""},
        ):
            with self.subTest(overrides=overrides):
                self.assertEqual(400, self.request_signature(**overrides).status_code)
        self.assertEqual(400, self.client.post("/presence/token/").status_code)

    def test_stale_key_returns_current_key(self):
        response = self.request_signature(key_id=str(int(self.key["key_id"]) - 1))
        self.assertEqual(409, response.status_code)
        self.assertEqual(self.key["key_id"], response.data["key"]["key_id"])
        self.assertEqual(self.key["public_key"], response.data["key"]["public_key"])

    def test_issuance_rate_limited_per_user(self):
        for _ in range(store.TOKEN_ISSUE_HOURLY_LIMIT):
            self.assertEqual(200, self.request_signature().status_code)
        self.assertEqual(429, self.request_signature().status_code)
        other = User.objects.create_user("other", "other@seas.upenn.edu", "other")
        PresenceOptIn.set_for_user(other, True, settings.PRESENCE_PRIVACY_POLICY_VERSION)
        self.client.force_authenticate(user=other)
        self.assertEqual(200, self.request_signature().status_code)
