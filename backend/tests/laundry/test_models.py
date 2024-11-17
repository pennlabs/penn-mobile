from django.test import TestCase

from laundry.models import LaundryRoom, LaundrySnapshot


class LaundrySnapshotTestCase(TestCase):
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
        self.laundry_room = LaundryRoom.objects.get(room_id=14089)
        self.snapshot = LaundrySnapshot.objects.create(
            room=self.laundry_room, available_washers=3, available_dryers=3
        )

    def test_str(self):
        self.assertEqual(
            str(self.snapshot),
            f"Room {self.snapshot.room.name} | {self.snapshot.date.date()}",
        )


class LaundryRoomTestCase(TestCase):
    def setUp(self):
        # populates database with LaundryRooms

        self.room = LaundryRoom.objects.create(
            room_id=14089,
            name="English House",
            location="English House",
            location_id=14146,
            total_washers=3,
            total_dryers=3,
        )

    def test_str(self):
        self.assertEqual(str(self.room), f"Room {self.room.name} | {self.room.location}")
