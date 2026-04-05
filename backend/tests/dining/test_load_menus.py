from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from dining.api_wrapper import DiningAPIWrapper
from dining.models import DiningMenu, Venue


def _make_response(venue_id, date_str, dayparts):
    return {
        "menus": {
            "items": {},
            "days": [
                {
                    "date": date_str,
                    "cafes": {str(venue_id): {"dayparts": [dayparts]}},
                }
            ],
        }
    }


class TestLoadMenus(TestCase):
    def test_load_menus_idempotent(self):
        """
        Calling `load_menus` twice should not create duplicate menus.
        """
        # Make some new venues
        venues = [
            Venue.objects.create(venue_id=2001, name="Hill", image_url="http://x"),
            Venue.objects.create(venue_id=2002, name="English", image_url="http://x"),
            Venue.objects.create(venue_id=2003, name="Lauder", image_url="http://x"),
        ]

        date = timezone.now().date()
        date_str = date.isoformat()

        # Each venue will have two meals/dayparts
        dayparts = [
            {"starttime": "08:00", "endtime": "10:00", "label": "Breakfast", "stations": []},
            {"starttime": "10:00", "endtime": "14:00", "label": "Lunch", "stations": []},
        ]

        # fetch a fake response for these menus
        def fake_fetch(self, venue_id, d):
            dayparts_copy = [dict(dp) for dp in dayparts]
            return (venue_id, _make_response(venue_id, date_str, dayparts_copy))

        # load menus twice
        with patch.object(DiningAPIWrapper, "fetch_menu", new=fake_fetch):
            wrapper = DiningAPIWrapper()
            wrapper.load_menus(date)
            count_after_first = DiningMenu.objects.filter(date=date).count()

            wrapper.load_menus(date)
            count_after_second = DiningMenu.objects.filter(date=date).count()

        # there should be the same amount pre-fetch and post-fetch
        expected = len(venues) * len(dayparts)
        self.assertEqual(count_after_first, expected)
        self.assertEqual(count_after_second, expected)

    def test_delete_duplicate_menus(self):
        """
        `delete_duplicate_menus` should remove all but the most recently
        created menu for duplicate menu groups on the same date.
        """
        venue = Venue.objects.create(venue_id=9001, name="Dup", image_url="http://x")

        date = timezone.now().date()

        start_time = timezone.now()
        end_time = start_time + timedelta(hours=1)

        # Create three duplicate menus (same venue, date, times, service).
        menus = [
            DiningMenu.objects.create(
                venue=venue,
                date=date,
                start_time=start_time,
                end_time=end_time,
                service="Dinner",
            )
            for _ in range(3)
        ]

        # Confrim we created 3 menus
        self.assertEqual(DiningMenu.objects.filter(venue=venue, date=date).count(), 3)

        wrapper = DiningAPIWrapper()
        deleted_count = wrapper.delete_duplicate_menus(date)

        # Two should be deleted, one should remain
        self.assertEqual(deleted_count, 2)
        remaining = DiningMenu.objects.filter(venue=venue, date=date)
        self.assertEqual(remaining.count(), 1)

        # The remaining menu should be the one with the highest id
        kept_id = max(m.id for m in menus)
        self.assertEqual(remaining.first().id, kept_id)
