# import csv
# import unittest

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from laundry.models import LaundryRoom, LaundrySnapshot


def fakeLaundryGet(url, *args, **kwargs):
    if "suds.kite.upenn.edu" in url:
        with open("tests/laundry/laundry_snapshot.html", "rb") as f:
            m = mock.MagicMock(content=f.read())
            print(m)
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
