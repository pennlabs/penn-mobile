import csv
import json
from io import StringIO
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from laundry.models import LaundryRoom, LaundrySnapshot


def mock_laundry_get(url, *args, **kwargs):
    # TODO: should we do this with regex? using split bc I think it's cleaner
    split = url.split("/")
    if "/".join(split[0:3]) == settings.LAUNDRY_URL:
        if split[3] == "rooms":
            with open(f"tests/laundry/mock_rooms_request_{split[4]}.json", "rb") as f:
                return json.load(f)
        elif split[3] == "geoBoundaries":
            with open("tests/laundry/mock_geoboundaries_request.json", "rb") as f:
                return json.load(f)
        else:
            raise NotImplementedError


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class TestGetSnapshot(TestCase):
    def setUp(self):
        # populates database with LaundryRooms
        LaundryRoom.objects.get_or_create(
            room_id=14089,
            name="English House",
            location="English House",
            location_id=14146,
            total_washers=3,
            total_dryers=3,
        )

        LaundryRoom.objects.get_or_create(
            room_id=14099,
            name="Harnwell 10th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )

        LaundryRoom.objects.get_or_create(
            room_id=14100,
            name="Harnwell 12th Floor",
            location="Harnwell College House",
            location_id=14150,
            total_washers=3,
            total_dryers=3,
        )

    def test_db_populate(self):
        out = StringIO()
        call_command("get_snapshot", stdout=out)

        # tests the value of the output
        self.assertEqual("Captured snapshots!\n", out.getvalue())

        # asserts that all rooms have been snapshotted
        self.assertEqual(LaundrySnapshot.objects.all().count(), 3)


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class TestLaundryRoomMigration(TestCase):
    def test_db_populate(self):
        out = StringIO()
        call_command("load_laundry_rooms", stdout=out)

        # tests the value of the output
        self.assertEqual("Uploaded Laundry Rooms!\n", out.getvalue())

        # compute expected number of rooms
        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.reader(data)
            # subtract 1 to account for header
            num_rooms = sum(1 for _ in reader) - 1

        # asserts that the number of LaundryRooms created was 53
        self.assertEqual(LaundryRoom.objects.all().count(), num_rooms)

        with open("laundry/data/laundry_data.csv") as data:
            reader = csv.DictReader(data)

            for row in reader:
                room = LaundryRoom.objects.get(room_id=int(row["room_id"]))

                # asserts that all fields of LaundryRoom are same
                self.assertEqual(room.name, row["room_name"])
                self.assertEqual(room.location, row["room_description"])
                self.assertEqual(room.location_id, int(row["room_location"]))
                self.assertEqual(room.total_washers, int(row["count_washers"]))
                self.assertEqual(room.total_dryers, int(row["count_dryers"]))
        call_command("load_laundry_rooms")

        # asserts that LaundryRooms do not recreate itself
        self.assertEqual(LaundryRoom.objects.all().count(), num_rooms)


@mock.patch("laundry.management.commands.update_laundry_rooms.get_validated", mock_laundry_get)
class TestUpdateLaundryRooms(TestCase):
    @mock.patch("laundry.management.commands.update_laundry_rooms.write_file")
    def test_update_laundry_rooms(self, mock_laundry_write):
        call_command("update_laundry_rooms")
        expected = [
            {
                "room_id": 14089,
                "room_name": "English House",
                "room_description": "English House",
                "room_location": 14146,
                "count_washers": 3,
                "count_dryers": 3,
            },
            {
                "room_id": 14099,
                "room_name": "Harnwell 10th Floor",
                "room_description": "Harnwell College House",
                "room_location": 14150,
                "count_washers": 3,
                "count_dryers": 3,
            },
            {
                "room_id": 14100,
                "room_name": "Harnwell 12th Floor",
                "room_description": "Harnwell College House",
                "room_location": 14150,
                "count_washers": 3,
                "count_dryers": 3,
            },
        ]
        # assert that the mock was called with this
        mock_laundry_write.assert_called_with(expected)
