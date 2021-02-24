import os

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from laundry.api_wrapper import all_status, hall_status, save_data
from laundry.models import LaundryRoom, LaundrySnapshot


LAUNDRY_URL = os.environ.get("LAUNDRY_URL", "http://suds.kite.upenn.edu")
ALL_URL = f"{LAUNDRY_URL}/?location="


class TestAllStatus(TestCase):
    def setUp(self):
        call_command("load_laundry_rooms")

    def test_all_status(self):
        
        data = all_status()

        self.assertEqual(len(data), 53)

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


class TestHallStatus(TestCase):
    def setUp(self):
        call_command("load_laundry_rooms")

    def test_all_status(self):

        for room in LaundryRoom.objects.all():

            # asserts fields are present
            status = hall_status(room.hall_id)
            machines = status["machines"]
            self.assertTrue("washers" in machines)
            self.assertTrue("dryers" in machines)

            for machine in machines["details"]:
                self.assertTrue("id" in machine)
                self.assertTrue("type" in machine)
                self.assertTrue("status" in machine)


class TestSaveData(TestCase):
    def setUp(self):
        call_command("load_laundry_rooms")

    def test_save_data(self):

        self.assertEqual(LaundrySnapshot.objects.all().count(), 0)

        save_data()

        # checks that all rooms have been accounted for
        self.assertEqual(LaundrySnapshot.objects.all().count(), 53)

        # # adds all id's to a list
        hall_ids = LaundryRoom.objects.all().values_list("hall_id", flat=True)

        self.assertEqual(len(hall_ids), 53)

        now = timezone.now().date()

        # asserts that fields are correct, and that all snapshots
        # have been accounted for
        for snapshot in LaundrySnapshot.objects.all():
            self.assertTrue(snapshot.room.hall_id in hall_ids)
            self.assertEqual(now, snapshot.date.date())
            self.assertTrue(snapshot.available_washers >= 0)
            self.assertTrue(snapshot.available_dryers >= 0)

        save_data()

        self.assertEqual(LaundrySnapshot.objects.all().count(), 106)
