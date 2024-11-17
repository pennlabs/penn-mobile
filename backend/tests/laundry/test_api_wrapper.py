from unittest import mock

from django.test import TestCase

from laundry.api_wrapper import all_status, room_status, save_data
from laundry.models import LaundryRoom, LaundrySnapshot
from tests.laundry.test_commands import mock_laundry_get


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class TestAllStatus(TestCase):
    def setUp(self):
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

    def test_all_status(self):

        data = all_status()

        self.assertEqual(len(data), 3)

        for room in LaundryRoom.objects.all():
            self.assertIn(room.name, data)

        # asserts fields are present and are positive numbers
        for hall_name, hall in data.items():
            for machine in ["washers", "dryers"]:
                data = hall[machine]

                self.assertIn("running", data)
                self.assertTrue(hall[machine]["running"] >= 0)

                self.assertIn("open", data)
                self.assertTrue(hall[machine]["open"] >= 0)

                self.assertIn("out_of_order", data)
                self.assertTrue(hall[machine]["out_of_order"] >= 0)

                self.assertIn("offline", data)
                self.assertTrue(hall[machine]["offline"] >= 0)


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class TestHallStatus(TestCase):
    def setUp(self):
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

    def test_all_status(self):

        for room in LaundryRoom.objects.all():

            # asserts fields are present
            status = room_status(room)
            machines = status["machines"]
            self.assertIn("washers", machines)
            self.assertIn("dryers", machines)

            for machine in machines["details"]:
                self.assertIn("id", machine)
                self.assertIn("type", machine)
                self.assertIn("status", machine)


@mock.patch("laundry.api_wrapper.get_validated", mock_laundry_get)
class TestSaveData(TestCase):
    def setUp(self):
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

    def test_save_data(self):

        self.assertEqual(LaundrySnapshot.objects.all().count(), 0)

        save_data()

        # checks that all rooms have been accounted for
        self.assertEqual(LaundrySnapshot.objects.all().count(), 3)

        # # adds all id's to a list
        room_ids = LaundryRoom.objects.all().values_list("room_id", flat=True)

        self.assertEqual(len(room_ids), 3)

        # asserts that fields are correct, and that all snapshots
        # have been accounted for
        for snapshot in LaundrySnapshot.objects.all():
            self.assertIn(snapshot.room.room_id, room_ids)
            self.assertTrue(snapshot.available_washers >= 0)
            self.assertTrue(snapshot.available_dryers >= 0)

        save_data()

        self.assertEqual(LaundrySnapshot.objects.all().count(), 6)
