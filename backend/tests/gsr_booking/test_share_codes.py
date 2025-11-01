import json
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from gsr_booking.models import GSR, Group, GSRBooking, GSRShareCode, Reservation
from gsr_booking.serializers import GSRShareCodeSerializer


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
        self.client.force_authenticate(user=self.owner)

    def test_create_share_code_success(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(reverse("share-create"), {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 201)
        payload = json.loads(response.content)

        self.assertIn("code", payload)
        self.assertTrue(GSRShareCode.objects.filter(code=payload["code"]).exists())

        response_again = self.client.post(reverse("share-create"), {"booking_id": self.booking.id})
        self.assertEqual(response_again.status_code, 200)
        payload_again = json.loads(response_again.content)
        self.assertEqual(payload_again["code"], payload["code"])

    def test_create_share_code_forbidden_for_non_owner(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.post(reverse("share-create"), {"booking_id": self.booking.id})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(GSRShareCode.objects.count(), 0)
        self.client.force_authenticate(user=self.owner)

    def test_view_shared_booking(self):
        self.client.force_authenticate(user=self.owner)
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        response = self.client.get(reverse("share-view", args=[share_code.code]))
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["room_name"], self.booking.room_name)
        self.assertEqual(payload["building"], self.booking.gsr.name)

    def test_view_shared_booking_invalid_or_expired(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(reverse("share-view", args=["INVALID"]))
        self.assertEqual(response.status_code, 404)

        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )
        self.booking.end = timezone.now() - timedelta(minutes=5)
        self.booking.save(update_fields=["end"])

        expired_response = self.client.get(reverse("share-view", args=[share_code.code]))
        self.assertEqual(expired_response.status_code, 400)

    def test_revoke_share_code(self):
        self.client.force_authenticate(user=self.owner)
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        response = self.client.delete(reverse("share-revoke", args=[share_code.code]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GSRShareCode.objects.filter(pk=share_code.pk).exists())

    def test_revoke_share_code_forbidden(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.owner,
        )

        self.client.force_authenticate(user=self.other)
        response = self.client.delete(reverse("share-revoke", args=[share_code.code]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(GSRShareCode.objects.filter(pk=share_code.pk).exists())
        self.client.force_authenticate(user=self.owner)


class ShareCodeModelSerializerTests(TestCase):
    def setUp(self):
        call_command("load_gsrs")
        self.user = User.objects.create_user("owner", password="one")
        self.booking = load_sample_booking(self.user)

    def test_generate_code_returns_unique_8_char_value(self):
        codes = {GSRShareCode.generate_code() for _ in range(5)}
        self.assertEqual(len(codes), 5)
        for code in codes:
            self.assertEqual(len(code), 8)

    def test_is_valid_and_serializer(self):
        share_code = GSRShareCode.objects.create(
            code=GSRShareCode.generate_code(),
            booking=self.booking,
            owner=self.user,
        )
        serializer = GSRShareCodeSerializer(share_code)
        self.assertEqual(serializer.data["status"], "active")
        expires_at = serializer.data["expires_at"]
        if isinstance(expires_at, str):
            parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = timezone.make_aware(parsed, timezone.utc)
            parsed = timezone.localtime(parsed)
            self.assertEqual(parsed, self.booking.end)
        else:
            self.assertEqual(timezone.localtime(expires_at), self.booking.end)

        self.booking.end = timezone.now() - timedelta(minutes=1)
        self.booking.save(update_fields=["end"])
        share_code.refresh_from_db()
        self.assertFalse(share_code.is_valid())
        serializer = GSRShareCodeSerializer(share_code)
        self.assertEqual(serializer.data["status"], "expired")
