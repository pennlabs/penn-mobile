import time
from unittest.mock import patch

import fakeredis
from django.test import TestCase
from rest_framework.test import APIClient

from presence import blind, store
from presence.models import Venue
from tests.presence.test_tokens import signed_token
from tests.presence.test_venues import GEOFENCE, HOURS


class HeartbeatTestCase(TestCase):
    def setUp(self):
        store._client = fakeredis.FakeStrictRedis(decode_responses=True)
        self.venue = Venue.objects.create(
            venue_id="pottruck", name="Pottruck", geofence=GEOFENCE, opening_hours=HOURS
        )
        self.signed = signed_token()
        self.token = self.signed["token"]

    def backdate(self, token, seconds):
        store._client.zadd("presence:active:pottruck", {token: time.time() - seconds})


class TestHeartbeatStore(HeartbeatTestCase):
    def test_heartbeat_marks_token_active(self):
        self.assertEqual("ok", store.heartbeat("pottruck", self.token))
        self.assertEqual(1, store.active_count("pottruck"))
        ttl = store._client.ttl(f"presence:token:{self.token}")
        self.assertTrue(0 < ttl <= store.TOKEN_TTL_SECONDS)

    def test_too_frequent_heartbeat_throttled(self):
        store.heartbeat("pottruck", self.token)
        self.assertEqual("throttled", store.heartbeat("pottruck", self.token))

    def test_heartbeat_allowed_after_interval(self):
        store.heartbeat("pottruck", self.token)
        self.backdate(self.token, store.HEARTBEAT_MIN_INTERVAL_SECONDS + 1)
        self.assertEqual("ok", store.heartbeat("pottruck", self.token))

    def test_stale_tokens_not_counted_and_pruned(self):
        store.heartbeat("pottruck", "stale")
        self.backdate("stale", store.ACTIVE_WINDOW_SECONDS + 1)
        self.assertEqual(0, store.active_count("pottruck"))
        store.heartbeat("pottruck", self.token)
        self.assertEqual([self.token], store._client.zrange("presence:active:pottruck", 0, -1))

    def test_rotation_transfers_presence_without_double_count(self):
        store.heartbeat("pottruck", self.token)
        self.assertEqual("ok", store.heartbeat("pottruck", "new", previous=self.token))
        self.assertEqual(1, store.active_count("pottruck"))
        self.assertEqual(["new"], store._client.zrange("presence:active:pottruck", 0, -1))

    def test_rotated_out_token_cannot_be_reused(self):
        store.heartbeat("pottruck", self.token)
        store.heartbeat("pottruck", "new", previous=self.token)
        self.assertEqual("invalid", store.heartbeat("pottruck", self.token))
        self.assertEqual(1, store.active_count("pottruck"))

    def test_unknown_previous_token_is_ignored(self):
        self.assertEqual("ok", store.heartbeat("pottruck", self.token, previous="never-seen"))
        self.assertEqual(1, store.active_count("pottruck"))
        self.assertFalse(store._client.exists("presence:token:never-seen"))

    def test_moving_venues_removes_previous_presence(self):
        store.heartbeat("pottruck", self.token)
        self.backdate(self.token, store.HEARTBEAT_MIN_INTERVAL_SECONDS + 1)
        self.assertEqual("ok", store.heartbeat("commons", self.token))
        self.assertEqual(0, store.active_count("pottruck"))
        self.assertEqual(1, store.active_count("commons"))

    def test_rotation_during_heartbeat_does_not_resurrect_token(self):
        store.heartbeat("pottruck", self.token)
        self.backdate(self.token, store.HEARTBEAT_MIN_INTERVAL_SECONDS + 1)
        original = store.client().pipeline
        rotated = False

        def interleave(*args, **kwargs):
            pipe = original(*args, **kwargs)
            execute = pipe.execute

            def rotate_before_commit(*args, **kwargs):
                nonlocal rotated
                if not rotated:
                    rotated = True
                    with patch.object(store.client(), "pipeline", original):
                        store.heartbeat("pottruck", "new", previous=self.token)
                return execute(*args, **kwargs)

            pipe.execute = rotate_before_commit
            return pipe

        with patch.object(store.client(), "pipeline", side_effect=interleave):
            self.assertEqual("invalid", store.heartbeat("pottruck", self.token))
        self.assertEqual(["new"], store._client.zrange("presence:active:pottruck", 0, -1))


class TestHeartbeatView(HeartbeatTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def heartbeat(self, **overrides):
        body = {"venue_id": "pottruck", **self.signed, **overrides}
        return self.client.post("/presence/heartbeat/", body, format="json")

    def test_no_authentication_required(self):
        self.assertEqual(204, self.heartbeat().status_code)
        self.assertEqual(1, store.active_count("pottruck"))

    def test_unsigned_or_forged_token_rejected(self):
        other = signed_token()
        for overrides in (
            {"token": "made-up-token-nobody-signed"},
            {"signature": other["signature"]},
            {"signature": "AAAA"},
            {"key_id": "0"},
        ):
            with self.subTest(overrides=overrides):
                self.assertEqual(403, self.heartbeat(**overrides).status_code)
        for missing in ({"signature": ""}, {"key_id": ""}, {"token": "short"}):
            self.assertEqual(400, self.heartbeat(**missing).status_code)
        self.assertEqual(0, store.active_count("pottruck"))

    def test_token_expires_with_its_signing_key(self):
        now = time.time()
        with patch("presence.blind.time.time", return_value=now + blind.KEY_EPOCH_SECONDS):
            self.assertEqual(204, self.heartbeat().status_code)
        with patch("presence.blind.time.time", return_value=now + 2 * blind.KEY_EPOCH_SECONDS):
            self.assertEqual(403, self.heartbeat().status_code)

    def test_rotation_carries_presence_and_retires_old_token(self):
        self.assertEqual(204, self.heartbeat().status_code)
        fresh = signed_token()
        self.assertEqual(204, self.heartbeat(**fresh, previous_token=self.token).status_code)
        self.assertEqual(1, store.active_count("pottruck"))
        self.backdate(self.token, store.HEARTBEAT_MIN_INTERVAL_SECONDS + 1)
        self.assertEqual(403, self.heartbeat().status_code)

    def test_unknown_venue(self):
        self.assertEqual(400, self.heartbeat(venue_id="nowhere").status_code)

    def test_disabled_venue(self):
        Venue.objects.filter(pk="pottruck").update(enabled=False)
        self.assertEqual(400, self.heartbeat().status_code)

    def test_too_frequent(self):
        self.heartbeat()
        self.assertEqual(429, self.heartbeat().status_code)
