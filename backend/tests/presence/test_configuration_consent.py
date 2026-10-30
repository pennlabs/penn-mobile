import json
import time
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import fakeredis
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.forms.models import model_to_dict
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from dining.models import Venue as DiningVenue
from penndata.models import FitnessRoom
from presence import store
from presence.admin import VenueAdmin, VenueForm
from presence.models import PresenceOptIn, Venue
from tests.presence.test_venues import GEOFENCE, HOURS, create_venue


class ConfigurationConsentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="presence-config-user")
        self.other = get_user_model().objects.create_user(username="other-presence-user")
        self.client = APIClient()
        store._client = fakeredis.FakeStrictRedis(decode_responses=True)
        self.policy = settings.PRESENCE_PRIVACY_POLICY_VERSION

    def post_consent(self, **data):
        return self.client.post("/api/presence/opt-in/", data, format="json")

    def import_records(self, records, **options):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "venues.json"
            path.write_text(json.dumps(records))
            call_command("import_tracked_locations", str(path), stdout=StringIO(), **options)

    def test_consent_access_ownership_and_heartbeat_contract(self):
        self.client.force_authenticate(self.user)
        missing = self.client.get("/api/presence/opt-in/").data
        self.assertEqual(missing["revision"], 0)
        self.assertIsNone(missing["updated_at"])
        self.assertEqual(PresenceOptIn.objects.count(), 0)
        other = PresenceOptIn.objects.create(user=self.other, opted_in=False)
        self.assertEqual(self.post_consent(opted_in=True, user=self.other.pk).status_code, 400)
        self.assertEqual(
            self.post_consent(opted_in=True, policy_version=self.policy).status_code, 200
        )
        other.refresh_from_db()
        self.assertFalse(other.opted_in)
        create_venue()
        token = self.client.post("/api/presence/token/", {}, format="json").data["token"]
        self.client.force_authenticate(None)
        received_after = time.time()
        response = self.client.post(
            "/api/presence/heartbeat/",
            {
                "venue_id": "pottruck",
                "token": token,
                "timestamp": "1900-01-01T00:00:00Z",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertGreaterEqual(
            store.client().zscore("presence:active:pottruck", token), received_after
        )
        # Another request can withdraw consent while this User instance is still cached.
        owner = get_user_model().objects.get(pk=self.user.pk)
        PresenceOptIn.set_for_user(owner, False)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post("/api/presence/token/").status_code, 403)

    def test_consent_transitions(self):
        self.client.force_authenticate(self.user)
        for version in ("", "outdated"):
            with self.subTest(version=version):
                self.assertEqual(
                    self.post_consent(opted_in=True, policy_version=version).status_code, 400
                )
        self.assertEqual(PresenceOptIn.objects.count(), 0)
        granted = self.post_consent(opted_in=True, policy_version=self.policy).data
        self.assertEqual(granted["revision"], 1)
        self.assertIsNotNone(granted["consented_at"])
        self.assertEqual(self.post_consent(opted_in=True, policy_version=self.policy).data, granted)
        with override_settings(PRESENCE_PRIVACY_POLICY_VERSION="presence-v2"):
            self.assertFalse(PresenceOptIn.is_opted_in(self.user))
            self.assertFalse(self.client.get("/api/presence/opt-in/").data["opted_in"])
            self.assertEqual(self.client.post("/api/presence/token/").status_code, 403)
            renewed = self.post_consent(opted_in=True, policy_version="presence-v2").data
            self.assertEqual(renewed["revision"], 2)
            withdrawn = self.post_consent(opted_in=False, policy_version="outdated").data
            self.assertFalse(withdrawn["opted_in"])
            self.assertEqual(withdrawn["revision"], 3)
            self.assertEqual(withdrawn["policy_version"], "presence-v2")
            self.assertEqual(self.post_consent(opted_in=False).data, withdrawn)
            self.assertEqual(self.client.post("/api/presence/token/").status_code, 403)

    def test_venue_configuration(self):
        gym = create_venue(kind="gym")
        room = FitnessRoom.objects.create(name="Example fitness room")
        gym.fitness_rooms.add(room)
        source = DiningVenue.objects.create(
            venue_id=593, name="Commons", image_url="https://example.com"
        )
        Venue.objects.create(
            venue_id="1920-commons",
            name="Commons",
            kind="dining",
            dining_venue=source,
            geofence=GEOFENCE,
            opening_hours=HOURS,
        )
        Venue.objects.create(venue_id="van-pelt", name="Van Pelt", kind="library", enabled=False)
        self.client.force_authenticate(self.user)
        with self.assertNumQueries(2):
            response = self.client.get("/api/presence/venues/")
        self.assertEqual(response.status_code, 200)
        venues = {venue["venue_id"]: venue for venue in response.data}
        self.assertEqual(set(venues), {"pottruck", "1920-commons"})
        self.assertEqual(venues["1920-commons"]["dining_venue_id"], 593)
        self.assertEqual(venues["pottruck"]["max_accuracy_m"], 50)
        self.assertEqual(venues["pottruck"]["fitness_room_ids"], [room.pk])
        self.assertEqual(PresenceOptIn.objects.count(), 0)
        # Include the hidden original values posted by Django's JSON widgets.
        data = model_to_dict(gym, exclude=["fitness_rooms"])
        for field in ("geofence", "opening_hours", "calibration"):
            data[field] = json.dumps(getattr(gym, field))
            data["initial-" + field] = data[field]
        another = FitnessRoom.objects.create(name="Another fitness room")
        data["fitness_rooms"] = [room.pk, another.pk]
        model_admin = VenueAdmin(Venue, admin.site)
        for _ in range(2):
            form = VenueForm(data=data, instance=gym)
            self.assertTrue(form.is_valid(), form.errors)
            gym = form.save(commit=False)
            model_admin.save_model(None, gym, form, change=True)
            model_admin.save_related(None, form, [], change=True)
            self.assertEqual(gym.configuration_version, 2, form.changed_data)
        for fields in (
            {"geofence": {}},
            {"geofence": {**GEOFENCE, "lat": float("nan")}},
            {"geofence": {**GEOFENCE, "radius_m": -1}},
            {"geofence": {"latitude": 40}},
            {"opening_hours": {}},
            {"opening_hours": []},
            {"opening_hours": {**HOURS, "weekly": {"7": []}}},
            {"max_accuracy_m": float("inf")},
        ):
            with self.subTest(fields=fields):
                config = {"geofence": GEOFENCE, "opening_hours": HOURS, **fields}
                invalid = Venue(venue_id="invalid", name="Invalid", **config)
                with self.assertRaises(ValidationError):
                    invalid.full_clean()

    def test_importer_safety(self):
        call_command("load_venues", stdout=StringIO())
        call_command("load_fitness_rooms", stdout=StringIO())
        call_command("import_tracked_locations", dry_run=True, stdout=StringIO())
        self.assertEqual(Venue.objects.count(), 0)
        for _ in range(2):
            call_command("import_tracked_locations", stdout=StringIO())
        self.assertEqual(Venue.objects.count(), 4)
        self.assertFalse(Venue.objects.filter(enabled=True).exists())
        pottruck = Venue.objects.get(pk="pottruck")
        self.assertEqual(pottruck.fitness_rooms.count(), 12)
        self.assertEqual(pottruck.configuration_version, 1)
        commons = Venue.objects.get(pk="1920-commons")
        self.assertEqual(commons.dining_venue_id, 593)
        update = {"venue_id": commons.pk, "name": "Updated Commons"}
        self.import_records([update], dry_run=True)
        commons.refresh_from_db()
        self.assertEqual(commons.name, "1920 Commons")
        self.import_records([update])
        self.import_records([update])
        commons.refresh_from_db()
        self.assertEqual(commons.configuration_version, 2)
        for invalid in (
            {"venue_id": "bad-dining", "name": "Bad", "kind": "dining", "dining_venue_id": -1},
            {
                "venue_id": "bad-gym",
                "name": "Bad",
                "kind": "gym",
                "fitness_room_names": ["Missing"],
            },
            {"venue_id": "bad-library", "name": "Bad", "enabled": True},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(CommandError):
                    self.import_records([{"venue_id": commons.pk, "name": "Roll back"}, invalid])
                commons.refresh_from_db()
                self.assertEqual(commons.name, "Updated Commons")
                self.assertEqual(Venue.objects.count(), 4)
        duplicate = {
            "name": "Duplicate",
            "dining_venue_id": 636,
            "kind": "dining",
            "enabled": False,
        }
        with self.assertRaises(CommandError):
            self.import_records(
                [{**duplicate, "venue_id": slug} for slug in ("duplicate-1", "duplicate-2")],
                dry_run=True,
            )
