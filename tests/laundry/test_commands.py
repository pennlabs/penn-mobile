import csv
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from laundry.models import LaundryRoom, LaundrySnapshot


class TestGetSnapshot(TestCase):
    def setUp(self):
        # populates database with LaundryRooms
        call_command("load_laundry_rooms")

    def test_call_command(self):
        out = StringIO()
        call_command("get_snapshot", stdout=out)

        # tests the value of the output
        self.assertEqual("Captured snapshots!\n", out.getvalue())

    def test_db_populate(self):
        call_command("get_snapshot")

        # asserts that all rooms have been snapshotted
        self.assertEqual(LaundrySnapshot.objects.all().count(), 53)

        now = timezone.now().date()

        # asserts that all snapshots have the same date (today)
        for snapshot in LaundrySnapshot.objects.all():
            self.assertEqual(snapshot.date.date(), now)


class TestUUIDMigration(TestCase):
    def test_call_command(self):
        out = StringIO()
        call_command("load_laundry_rooms", stdout=out)

        # tests the value of the output
        self.assertEqual("Uploaded Laundry Rooms!\n", out.getvalue())

    def test_db_populate(self):
        call_command("load_laundry_rooms")

        # asserts that the number of LaundryRooms created was 53
        self.assertEqual(LaundryRoom.objects.all().count(), 53)

        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.reader(data)

            for i, row in enumerate(reader):
                hall_id, hall_name, location, uuid = row

                room = LaundryRoom.objects.get(hall_id=hall_id)

                # asserts that all fields of LaundryRoom are same
                self.assertEqual(room.name, hall_name)
                self.assertEqual(room.location, location)
                self.assertEqual(str(room.uuid), uuid)

        call_command("load_laundry_rooms")

        # asserts that LaundryRooms do not recreate itself
        self.assertEqual(LaundryRoom.objects.all().count(), 53)
