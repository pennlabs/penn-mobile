from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from dining.models import Venue


class TestLoadVenues(TestCase):
    def test(self):
        out = StringIO()
        call_command("load_venues", stdout=out)

        self.assertEqual(len(Venue.objects.all()), 16)

        list_of_ids = []
        for venue in Venue.objects.all():
            self.assertNotIn(venue.venue_id, list_of_ids)
            list_of_ids.append(venue.venue_id)

        call_command("load_venues", stdout=out)

        # load_venues script should be idempotent
        self.assertEqual(len(Venue.objects.all()), 16)
        self.assertEqual("1920 Commons-593", str(Venue.objects.get(venue_id=593)))
