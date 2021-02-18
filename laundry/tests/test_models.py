from django.test import TestCase

from laundry.models import LaundryRoom, LaundrySnapshot


class LaundrySnapshotTestCase(TestCase):
    def setUp(self):
        print('here')
        self.snapshot = LaundrySnapshot.objects.create(
            hall_id=1, available_washers=10, available_dryers=10, total_washers=20, total_dryers=20
        )

    def test_str(self):
        self.assertEqual(
            str(self.snapshot), f"Hall No. {self.snapshot.hall_id} | {self.date.date()}",
        )


class LaundryRoomTestCase(TestCase):
    def setUp(self):
        self.room = LaundryRoom.objects.create(hall_id=1, name="test hall", location="location")

    def test_str(self):
        self.assertEqual(
            str(self.room), f"Hall No. {self.room.hall_id} | {self.room.name}",
        )
