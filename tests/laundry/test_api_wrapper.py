import os
# import unittest
from unittest import mock

from django.test import TestCase

from laundry.api_wrapper import all_status, hall_status, save_data
from laundry.models import LaundryRoom, LaundrySnapshot
from tests.laundry.test_commands import fakeLaundryGet


LAUNDRY_URL = os.environ.get("LAUNDRY_URL", "http://suds.kite.upenn.edu")
ALL_URL = f"{LAUNDRY_URL}/?location="


@mock.patch("requests.get", fakeLaundryGet)
class TestAllStatus(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of ***REMOVED***8 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )

    def test_all_status(self):

        data = all_status()

        self.assertEqual(len(data), 4)

        for room in LaundryRoom.objects.all():
            self.assertTrue(room.name in data)

        # asserts fields are present and are positive numbers
        for hall_name, hall in data.items():
            for machine in ["washers", "dryers"]:
                data = hall[machine]

                self.assertTrue("running" in data)
                self.assertTrue(hall[machine]["running"] >= 0)

                self.assertTrue("open" in data)
                self.assertTrue(hall[machine]["open"] >= 0)

                self.assertTrue("out_of_order" in data)
                self.assertTrue(hall[machine]["out_of_order"] >= 0)

                self.assertTrue("offline" in data)
                self.assertTrue(hall[machine]["offline"] >= 0)


@mock.patch("requests.get", fakeLaundryGet)
class TestHallStatus(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of ***REMOVED***8 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )

    def test_all_status(self):

        for room in LaundryRoom.objects.all():

            # asserts fields are present
            status = hall_status(room)
            machines = status["machines"]
            self.assertTrue("washers" in machines)
            self.assertTrue("dryers" in machines)

            for machine in machines["details"]:
                self.assertTrue("id" in machine)
                self.assertTrue("type" in machine)
                self.assertTrue("status" in machine)


@mock.patch("requests.get", fakeLaundryGet)
class TestSaveData(TestCase):
    def setUp(self):
        LaundryRoom.objects.get_or_create(
            hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
        )
        LaundryRoom.objects.get_or_create(
            hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
        )
        LaundryRoom.objects.get_or_create(
            hall_id=2, name="Class of ***REMOVED***8 Fisher", location="Quad", total_washers=8, total_dryers=8
        )
        LaundryRoom.objects.get_or_create(
            hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
        )

    def test_save_data(self):

        self.assertEqual(LaundrySnapshot.objects.all().count(), 0)

        save_data()

        # checks that all rooms have been accounted for
        self.assertEqual(LaundrySnapshot.objects.all().count(), 4)

        # # adds all id's to a list
        hall_ids = LaundryRoom.objects.all().values_list("hall_id", flat=True)

        self.assertEqual(len(hall_ids), 4)

        # asserts that fields are correct, and that all snapshots
        # have been accounted for
        for snapshot in LaundrySnapshot.objects.all():
            self.assertTrue(snapshot.room.hall_id in hall_ids)
            self.assertTrue(snapshot.available_washers >= 0)
            self.assertTrue(snapshot.available_dryers >= 0)

        save_data()

        self.assertEqual(LaundrySnapshot.objects.all().count(), 8)
