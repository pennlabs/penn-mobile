import json
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from gsr_booking.models import GSR, Group, GSRBooking, GSRShareCode, Reservation
from gsr_booking.serializers import GSRShareCodeSerializer, SharedGSRBookingSerializer


User = get_user_model()


def load_sample_booking(owner):
    with open("tests/gsr_booking/views_reservations.json") as data:
        first = json.load(data)[0]

    gsr = GSR.objects.get(gid=first["gsr"]["gid"])
    start_raw = datetime.fromisoformat(first["start"].replace("Z", "+00:00"))
    end_raw = datetime.fromisoformat(first["end"].replace("Z", "+00:00"))
    if start_raw.tzinfo is None:
        start_raw = timezone.make_aware(start_raw, timezone.utc)
    if end_raw.tzinfo is None:
        end_raw = timezone.make_aware(end_raw, timezone.utc)
    duration = end_raw - start_raw

    start = timezone.localtime() + timedelta(hours=1)
    end = start + duration
    reservation = Reservation.objects.create(start=start, end=end, creator=owner)
    return GSRBooking.objects.create(
        reservation=reservation,
        user=owner,
        booking_id=first["booking_id"],
        gsr=gsr,
        room_id=first["room_id"],
        room_name=first["room_name"],
        start=start,
        end=end,
    )


class ShareCodeViewTests(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.client = APIClient()
        self.owner = User.objects.create_user("owner", password="one")
        self.other = User.objects.create_user("other", password="two")
        Group.objects.create(owner=self.other, name="Penn Labs", color="blue")
        self.group = Group.objects.create(owner=self.owner, name="group", color="blue")

        self.booking = load_sample_booking(self.owner)

    def test_create_share_code_success(self):
        # Creates a gsr share code successfully
        self.client.force_authenticate(user=self.owner)
        response = self.client.post("/api/gsr/share/", {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 201)
        payload = json.loads(response.content)

        self.assertIn("code", payload)
        self.assertIn("created_at", payload)
        self.assertIn("expires_at", payload)
        self.assertIn("status", payload)
        self.assertEqual(payload["status"], "active")
        self.assertEqual(len(payload["code"]), 8)
        self.assertTrue(GSRShareCode.objects.filter(code=payload["code"]).exists())

    def test_create_share_code_duplicate(self):
        self.client.force_authenticate(user=self.owner)

        # First creation
        response1 = self.client.post("/api/gsr/share/", {"booking_id": self.booking.id})
        self.assertEqual(response1.status_code, 201)
        payload1 = json.loads(response1.content)
        first_code = payload1["code"]

        # Second creation (should return existing code)
        response2 = self.client.post("/api/gsr/share/", {"booking_id": self.booking.id})
        self.assertEqual(response2.status_code, 200)
        payload2 = json.loads(response2.content)

        # Should be the same code
        self.assertEqual(payload2["code"], first_code)

        # exist only one code in database
        self.assertEqual(GSRShareCode.objects.filter(booking=self.booking).count(), 1)

    def test_create_share_code_without_auth(self):
        response = self.client.post("/api/gsr/share/", {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(GSRShareCode.objects.count(), 0)

    def test_create_share_code_invalid_booking(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post("/api/gsr/share/", {"booking_id": 99999})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GSRShareCode.objects.count(), 0)

    def test_create_share_code_missing_booking_id(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post("/api/gsr/share/", {})
        self.assertEqual(response.status_code, 400)

    def test_view_shared_booking_public_access(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        # No auth
        response = self.client.get(f"/api/gsr/share/{share_code.code}/")
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)

        # Should only contain booking info and not owner info
        self.assertIn("room_name", payload)
        self.assertIn("building", payload)
        self.assertIn("start", payload)
        self.assertIn("end", payload)
        self.assertIn("is_valid", payload)
        self.assertEqual(payload["room_name"], self.booking.room_name)
        self.assertEqual(payload["building"], self.booking.gsr.name)
        self.assertEqual(payload["is_valid"], True)

    def test_view_shared_booking_invalid_code(self):
        response = self.client.get("/api/gsr/share/INVALID1/")
        self.assertEqual(response.status_code, 404)

    def test_view_shared_booking_wrong_format_code(self):
        # Too short
        response = self.client.get("/api/gsr/share/abc/")
        self.assertEqual(response.status_code, 404)

        # Too long
        response = self.client.get("/api/gsr/share/abcdefghijk/")
        self.assertEqual(response.status_code, 404)

        # Invalid characters
        response = self.client.get("/api/gsr/share/abc@%23$%25%5E/")
        self.assertEqual(response.status_code, 404)

    def test_view_expired_share_code(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        # Make booking expired
        self.booking.end = timezone.now() - timedelta(minutes=5)
        self.booking.save(update_fields=["end"])

        response = self.client.get(f"/api/gsr/share/{share_code.code}/")
        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertIn("error", payload)
        self.assertIn("expired", payload["error"].lower())

    def test_delete_share_code_as_owner(self):
        self.client.force_authenticate(user=self.owner)
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        response = self.client.delete(f"/api/gsr/share/{share_code.code}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(GSRShareCode.objects.filter(pk=share_code.pk).exists())

    def test_delete_share_code_as_non_owner(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f"/api/gsr/share/{share_code.code}/")
        # Returns 404, non-owners shouldn't see that the code exists
        self.assertEqual(response.status_code, 404)
        self.assertTrue(GSRShareCode.objects.filter(pk=share_code.pk).exists())

    def test_delete_share_code_without_auth(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        response = self.client.delete(f"/api/gsr/share/{share_code.code}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(GSRShareCode.objects.filter(pk=share_code.pk).exists())

    def test_view_deleted_share_code(self):
        self.client.force_authenticate(user=self.owner)
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )
        code = share_code.code

        # Delete the share code
        self.client.delete(f"/api/gsr/share/{code}/")

        # Try to view it
        response = self.client.get(f"/api/gsr/share/{code}/")
        self.assertEqual(response.status_code, 404)

    def test_create_share_code_for_expired_booking_code_invalid(self):
        self.booking.end = timezone.now() - timedelta(hours=1)
        self.booking.save(update_fields=["end"])

        self.client.force_authenticate(user=self.owner)
        response = self.client.post("/api/gsr/share/", {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 201)
        payload = json.loads(response.content)
        self.assertEqual(payload["status"], "expired")

    def test_retrieve_unauthenticated_valid_code(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        # No authentication
        response = self.client.get(f"/api/gsr/share/{share_code.code}/")
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertIn("room_name", payload)
        self.assertIn("is_valid", payload)

    def test_create_share_code_replaces_expired(self):
        # Create share code
        old_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )
        old_code_value = old_code.code

        # Create again
        self.client.force_authenticate(user=self.owner)
        response = self.client.post("/api/gsr/share/", {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)

        # Should return the same code
        self.assertEqual(payload["code"], old_code_value)
        # Should still only have one code
        self.assertEqual(GSRShareCode.objects.filter(booking=self.booking).count(), 1)


class ShareCodeModelSerializerTests(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.user = User.objects.create_user("owner", password="one")
        self.booking = load_sample_booking(self.user)

    def test_generate_code_returns_unique_8_char_value(self):
        codes = {GSRShareCode.generate_code() for _ in range(10)}
        self.assertEqual(len(codes), 10)  # all unique
        for code in codes:
            self.assertEqual(len(code), 8)
            self.assertTrue(all(c.isalnum() or c in "-_" for c in code))

    def test_share_code_serializer_active(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.user,
        )
        serializer = GSRShareCodeSerializer(share_code)

        self.assertEqual(serializer.data["status"], "active")
        self.assertEqual(serializer.data["code"], share_code.code)
        self.assertIn("created_at", serializer.data)
        self.assertIn("expires_at", serializer.data)

    def test_share_code_serializer_expired(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.user,
        )

        # Make booking expired
        self.booking.end = timezone.now() - timedelta(minutes=1)
        self.booking.save(update_fields=["end"])
        share_code.refresh_from_db()

        self.assertFalse(share_code.is_valid())
        serializer = GSRShareCodeSerializer(share_code)
        self.assertEqual(serializer.data["status"], "expired")

    def test_shared_booking_serializer(self):
        serializer = SharedGSRBookingSerializer(self.booking)
        data = serializer.data

        # Should have booking details
        self.assertIn("room_name", data)
        self.assertIn("building", data)
        self.assertIn("start", data)
        self.assertIn("end", data)
        self.assertIn("is_valid", data)

        # Should not have owner info
        self.assertNotIn("user", data)
        self.assertNotIn("owner", data)
        self.assertNotIn("reservation", data)
        self.assertNotIn("booking_id", data)

    def test_is_valid_method(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.user,
        )

        self.assertTrue(share_code.is_valid())

        # Make expired
        self.booking.end = timezone.now() - timedelta(seconds=1)
        self.booking.save(update_fields=["end"])

        self.assertFalse(share_code.is_valid())

    def test_shared_booking_serializer_expired(self):
        self.booking.end = timezone.now() - timedelta(hours=1)
        self.booking.save(update_fields=["end"])

        serializer = SharedGSRBookingSerializer(self.booking)
        self.assertFalse(serializer.data["is_valid"])
