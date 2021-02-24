from django.test import TestCase
from django.core.management import call_command

from laundry.models import LaundryRoom, LaundrySnapshot


class LaundrySnapshotTestCase(TestCase):
    def setUp(self):
        call_command("load_laundry_rooms")
        self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
        self.snapshot = LaundrySnapshot.objects.create(
            room=self.laundry_room,
            available_washers=10,
            available_dryers=10,
        )

    def test_str(self):
        self.assertEqual(
            str(self.snapshot),
            f"Hall No. {self.snapshot.room.hall_id} | {self.snapshot.date.date()}",
        )


class LaundryRoomTestCase(TestCase):
    def setUp(self):
        call_command("load_laundry_rooms")
        self.room = LaundryRoom.objects.create(hall_id=1, name="test hall", location="location")

    def test_str(self):
        self.assertEqual(
            str(self.room), f"Hall No. {self.room.hall_id} | {self.room.name}",
        )
