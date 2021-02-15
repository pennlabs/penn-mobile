import os

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from laundry.api_wrapper import Laundry
from laundry.models import LaundryRoom, LaundrySnapshot


LAUNDRY_URL = os.environ.get("LAUNDRY_URL", "http://suds.kite.upenn.edu")
ALL_URL = f"{LAUNDRY_URL}/?location="

# sets up the database and Laundry object
call_command("uuid_migration")
laundry = Laundry()


class TestInitialization(TestCase):
    def testLaundry(self):

        self.assertEqual(len(laundry.days), 7)

        for room in LaundryRoom.objects.all():

            # tests all fields are correct
            link = laundry.hall_to_link[room.name]
            self.assertEqual(link, ALL_URL + str(room.uuid))

            hall_id = laundry.id_to_hall[room.hall_id]
            self.assertEqual(room.name, hall_id)

            hall_location = laundry.id_to_location[room.hall_id]
            self.assertEqual(room.location, hall_location)

            hall_list = laundry.hall_id_list
            self.assertTrue(
                {"hall_name": room.name, "id": room.hall_id, "location": room.location} in hall_list
            )


class TestAllStatus(TestCase):
    def test_all_status(self):

        data = laundry.all_status()

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
    def test_all_status(self):

        for room in LaundryRoom.objects.all():

            # asserts fields are present
            status = laundry.hall_status(room.hall_id)
            machines = status["machines"]
            self.assertTrue("washers" in machines)
            self.assertTrue("dryers" in machines)

            for machine in machines["details"]:
                self.assertTrue("id" in machine)
                self.assertTrue("type" in machine)
                self.assertTrue("status" in machine)


class TestSaveData(TestCase):
    def test_save_data(self):

        self.assertEqual(LaundrySnapshot.objects.all().count(), 0)

        laundry.save_data()

        # checks that all rooms have been accounted for
        self.assertEqual(LaundrySnapshot.objects.all().count(), 53)

        # adds all id's to a list
        data = laundry.hall_id_list
        hall_ids = []
        for item in data:
            hall_ids.append(item["id"])

        self.assertEqual(len(hall_ids), 53)

        now = timezone.now().date()

        # asserts that fields are correct, and that all snapshots
        # have been accounted for
        for snapshot in LaundrySnapshot.objects.all():
            self.assertTrue(snapshot.hall_id in hall_ids)
            self.assertEqual(now, snapshot.date.date())
            self.assertTrue(snapshot.available_washers >= 0)
            self.assertTrue(snapshot.available_dryers >= 0)
            self.assertTrue(snapshot.total_dryers >= snapshot.available_dryers)
            self.assertTrue(snapshot.total_washers >= snapshot.available_washers)

        laundry.save_data()

        self.assertEqual(LaundrySnapshot.objects.all().count(), 106)
