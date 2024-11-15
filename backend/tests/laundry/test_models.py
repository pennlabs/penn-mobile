# from django.test import TestCase
#
# from laundry.models import LaundryRoom, LaundrySnapshot
#
#
# class LaundrySnapshotTestCase(TestCase):
#     def setUp(self):
#         # populates database with LaundryRooms
#         LaundryRoom.objects.get_or_create(
#             hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
#         )
#         LaundryRoom.objects.get_or_create(
#             hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
#         )
#         LaundryRoom.objects.get_or_create(
#             hall_id=2, name="Class of 1928 Fisher", location="Quad", total_washers=8, total_dryers=8
#         )
#         LaundryRoom.objects.get_or_create(
#             hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
#         )
#         self.laundry_room = LaundryRoom.objects.get(hall_id=0, name="Bishop White", location="Quad")
#         self.snapshot = LaundrySnapshot.objects.create(
#             room=self.laundry_room, available_washers=10, available_dryers=10
#         )
#
#     def test_str(self):
#         self.assertEqual(
#             str(self.snapshot),
#             f"Hall No. {self.snapshot.room.hall_id} | {self.snapshot.date.date()}",
#         )
#
#
# class LaundryRoomTestCase(TestCase):
#     def setUp(self):
#         # populates database with LaundryRooms
#         LaundryRoom.objects.get_or_create(
#             hall_id=0, name="Bishop White", location="Quad", total_washers=9, total_dryers=9
#         )
#         LaundryRoom.objects.get_or_create(
#             hall_id=1, name="Chestnut Butcher", location="Quad", total_washers=11, total_dryers=11
#         )
#         LaundryRoom.objects.get_or_create(
#             hall_id=2, name="Class of 1928 Fisher", location="Quad", total_washers=8, total_dryers=8
#         )
#         LaundryRoom.objects.get_or_create(
#             hall_id=3, name="Craig", location="Quad", total_washers=3, total_dryers=3
#         )
#         self.room = LaundryRoom.objects.create(hall_id=1, name="test hall", location="location")
#
#     def test_str(self):
#         self.assertEqual(str(self.room), f"Hall No. {self.room.hall_id} | {self.room.name}")
