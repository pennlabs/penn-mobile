import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from presence.models import Venue


User = get_user_model()

GEOFENCE = {"lat": 39.9535, "lng": -75.1970, "radius_m": 60}


def create_venue(venue_id="pottruck", **kwargs):
    return Venue.objects.create(
        venue_id=venue_id, name=kwargs.pop("name", "Pottruck"), geofence=GEOFENCE, **kwargs
    )


class TestVenueModel(TestCase):
    def test_defaults(self):
        venue = create_venue()
        self.assertTrue(venue.enabled)
        self.assertEqual(180, venue.min_dwell_seconds)
        self.assertEqual(120, venue.exit_grace_seconds)
        self.assertEqual(5, venue.min_sample_size)
        self.assertEqual({}, venue.calibration)
        self.assertIsNone(venue.capacity)

    def test_venue_id_is_primary_key(self):
        create_venue()
        self.assertTrue(Venue.objects.filter(pk="pottruck").exists())

    def test_str(self):
        self.assertEqual("pottruck", str(create_venue()))


class TestVenueListView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(403, self.client.get("/presence/venues/").status_code)

    def test_lists_enabled_venues_with_client_fields(self):
        create_venue()
        response = self.client.get("/presence/venues/")
        self.assertEqual(200, response.status_code)
        venues = json.loads(response.content)
        self.assertEqual(1, len(venues))
        self.assertEqual(
            {
                "venue_id": "pottruck",
                "name": "Pottruck",
                "geofence": GEOFENCE,
                "min_dwell_seconds": 180,
                "exit_grace_seconds": 120,
            },
            venues[0],
        )

    def test_excludes_disabled_venues(self):
        create_venue()
        create_venue(venue_id="commons", name="1920 Commons", enabled=False)
        venues = json.loads(self.client.get("/presence/venues/").content)
        self.assertEqual(["pottruck"], [v["venue_id"] for v in venues])
