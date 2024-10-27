import csv
from io import StringIO
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from laundry.models import LaundryRoom, LaundrySnapshot


def fakeLaundryGet(url, *args, **kwargs):
    # TODO: should we do this with regex? using split bc I think it's cleaner
    split = url.split("/")
    if "/".join(split[0:3]) == settings.LAUNDRY_URL:
        if split[3] == "rooms":
            with open(f"tests/laundry/mock_rooms_request_{split[4]}.json", "rb") as f:
                m = mock.MagicMock(content=f.read())
                return m
        elif split[3] == "geoBoundaries":
            with open("tests/laundry/mock_geoboundaries_request.json", "rb") as f:
                m = mock.MagicMock(content=f.read())
                return m
        else:
            raise NotImplementedError


@mock.patch("requests.get", fakeLaundryGet)
class TestGetSnapshot(TestCase):
    def setUp(self):
        # populates database with LaundryRooms
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of 1928 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )

    def test_db_populate(self):
        out = StringIO()
        call_command("get_snapshot", stdout=out)

        # tests the value of the output
        self.assertEqual("Captured snapshots!\n", out.getvalue())

        # asserts that all rooms have been snapshotted
        self.assertEqual(LaundrySnapshot.objects.all().count(), 4)


@mock.patch("requests.get", fakeLaundryGet)
class TestLaundryRoomMigration(TestCase):
    def test_db_populate(self):
        out = StringIO()
        call_command("load_laundry_rooms", stdout=out)

        # tests the value of the output
        self.assertEqual("Uploaded Laundry Rooms!\n", out.getvalue())

        # asserts that the number of LaundryRooms created was 53
        self.assertEqual(LaundryRoom.objects.all().count(), 53)

        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.reader(data)

            for i, row in enumerate(reader):
                hall_id, hall_name, location, uuid, total_washers, total_dryers = row

                room = LaundryRoom.objects.get(hall_id=hall_id)

                # asserts that all fields of LaundryRoom are same
                self.assertEqual(room.name, hall_name)
                self.assertEqual(room.location, location)
                self.assertEqual(str(room.uuid), uuid)
                self.assertEqual(room.total_washers, int(total_washers))
                self.assertEqual(room.total_dryers, int(total_dryers))

        call_command("load_laundry_rooms")

        # asserts that LaundryRooms do not recreate itself
        self.assertEqual(LaundryRoom.objects.all().count(), 53)
