from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from dining.models import Venue


class TestLoadVenues(TestCase):
    def test(self):
        out = StringIO()
        call_command("load_venues", stdout=out)

        self.assertEqual(len(Venue.objects.all()), 14)

        list_of_ids = []
        for venue in Venue.objects.all():
            self.assertTrue(venue.venue_id not in list_of_ids)
            list_of_ids.append(venue.venue_id)

        call_command("load_venues", stdout=out)

        self.assertEqual(len(Venue.objects.all()), 14)
