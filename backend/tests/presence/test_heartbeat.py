import time
from unittest.mock import patch

import fakeredis
from django.test import TestCase
from rest_framework.test import APIClient

from presence import store
from presence.models import Venue


GEOFENCE = {"lat": 39.9535, "lng": -75.1970, "radius_m": 60}


class HeartbeatTestCase(TestCase):
    def setUp(self):
        store._client = fakeredis.FakeStrictRedis(decode_responses=True)
        self.venue = Venue.objects.create(venue_id="pottruck", name="Pottruck", geofence=GEOFENCE)
        self.token = store.issue_token()

    def backdate(self, token, seconds):
        store._client.zadd("presence:active:pottruck", {token: time.time() - seconds})


class TestHeartbeatStore(HeartbeatTestCase):
    def test_heartbeat_marks_token_active(self):
        self.assertEqual("ok", store.heartbeat("pottruck", self.token))
        self.assertEqual(1, store.active_count("pottruck"))

    def test_invalid_token(self):
        self.assertEqual("invalid", store.heartbeat("pottruck", "made-up"))
        self.assertEqual(0, store.active_count("pottruck"))

    def test_too_frequent_heartbeat_throttled(self):
        store.heartbeat("pottruck", self.token)
        self.assertEqual("throttled", store.heartbeat("pottruck", self.token))

    def test_heartbeat_allowed_after_interval(self):
        store.heartbeat("pottruck", self.token)
        self.backdate(self.token, store.HEARTBEAT_MIN_INTERVAL_SECONDS + 1)
        self.assertEqual("ok", store.heartbeat("pottruck", self.token))

    def test_stale_tokens_not_counted_and_pruned(self):
        stale = store.issue_token()
        store.heartbeat("pottruck", stale)
        self.backdate(stale, store.ACTIVE_WINDOW_SECONDS + 1)
        self.assertEqual(0, store.active_count("pottruck"))
        store.heartbeat("pottruck", self.token)
        self.assertEqual([self.token], store._client.zrange("presence:active:pottruck", 0, -1))

    def test_rotation_transfers_presence_without_double_count(self):
        store.heartbeat("pottruck", self.token)
        new = store.issue_token(previous=self.token)
        self.assertEqual(1, store.active_count("pottruck"))
        self.assertEqual([new], store._client.zrange("presence:active:pottruck", 0, -1))
        self.assertEqual("throttled", store.heartbeat("pottruck", new))

    def test_moving_venues_removes_previous_presence(self):
        store.heartbeat("pottruck", self.token)
        self.backdate(self.token, store.HEARTBEAT_MIN_INTERVAL_SECONDS + 1)
        self.assertEqual("ok", store.heartbeat("commons", self.token))
        self.assertEqual(0, store.active_count("pottruck"))
        self.assertEqual(1, store.active_count("commons"))

    def test_expiry_during_heartbeat_does_not_resurrect_token(self):
        original = store.client().pipeline
        expired = False

        def interleave(*args, **kwargs):
            pipe = original(*args, **kwargs)
            execute = pipe.execute

            def expire_before_commit(*args, **kwargs):
                nonlocal expired
                if not expired:
                    expired = True
                    store.client().delete(f"presence:token:{self.token}")
                return execute(*args, **kwargs)

            pipe.execute = expire_before_commit
            return pipe

        with patch.object(store.client(), "pipeline", side_effect=interleave):
            self.assertEqual("invalid", store.heartbeat("pottruck", self.token))
        self.assertFalse(store.is_valid_token(self.token))
        self.assertEqual(0, store.active_count("pottruck"))


class TestHeartbeatView(HeartbeatTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def heartbeat(self, **overrides):
        body = {"venue_id": "pottruck", "token": self.token, **overrides}
        return self.client.post("/presence/heartbeat/", body, format="json")

    def test_no_authentication_required(self):
        self.assertEqual(204, self.heartbeat().status_code)
        self.assertEqual(1, store.active_count("pottruck"))

    def test_invalid_token(self):
        self.assertEqual(403, self.heartbeat(token="made-up").status_code)

    def test_unknown_venue(self):
        self.assertEqual(400, self.heartbeat(venue_id="nowhere").status_code)

    def test_disabled_venue(self):
        Venue.objects.filter(pk="pottruck").update(enabled=False)
        self.assertEqual(400, self.heartbeat().status_code)

    def test_too_frequent(self):
        self.heartbeat()
        self.assertEqual(429, self.heartbeat().status_code)
