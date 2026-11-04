from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from gsr_booking.models import GSR, GSRBooking, GSRBookingShare, Reservation


User = get_user_model()


class GSRBookingShareTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password")
        self.recipient = User.objects.create_user(username="recipient", password="password")
        self.other = User.objects.create_user(username="other", password="password")
        self.client = APIClient()

        self.gsr = GSR.objects.create(
            lid="test-lid",
            gid=12345,
            name="Test Library",
            image_url="https://example.com/room.jpg",
        )
        self.reservation = Reservation.objects.create(
            creator=self.owner,
            start=timezone.now() + timedelta(hours=1),
            end=timezone.now() + timedelta(hours=2),
        )
        self.booking = GSRBooking.objects.create(
            reservation=self.reservation,
            user=self.owner,
            booking_id="booking-1",
            gsr=self.gsr,
            room_id=1,
            room_name="Room 1",
            start=self.reservation.start,
            end=self.reservation.end,
        )

    def test_owner_can_invite_user(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/gsr/booking-shares/",
            {"reservation": self.reservation.pk, "recipient": self.recipient.username},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], GSRBookingShare.PENDING)
        self.assertEqual(response.data["recipient"], self.recipient.username)
        self.assertEqual(len(response.data["bookings"]), 1)
        self.assertEqual(GSRBookingShare.objects.count(), 1)

    def test_only_reservation_owner_can_invite(self):
        self.client.force_authenticate(self.other)
        response = self.client.post(
            "/api/gsr/booking-shares/",
            {"reservation": self.reservation.pk, "recipient": self.recipient.username},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(GSRBookingShare.objects.exists())

    def test_invite_cannot_target_self(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/gsr/booking-shares/",
            {"reservation": self.reservation.pk, "recipient": self.owner.username},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(GSRBookingShare.objects.exists())

    def test_duplicate_invite_reuses_existing_share(self):
        self.client.force_authenticate(self.owner)
        payload = {"reservation": self.reservation.pk, "recipient": self.recipient.username}

        first = self.client.post("/api/gsr/booking-shares/", payload)
        second = self.client.post("/api/gsr/booking-shares/", payload)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(GSRBookingShare.objects.count(), 1)

    def test_invitee_can_accept_and_view_only_active_bookings(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation, inviter=self.owner, recipient=self.recipient
        )
        self.client.force_authenticate(self.recipient)

        pending = self.client.get(f"/api/gsr/booking-shares/{share.pk}/")
        self.assertEqual(pending.status_code, 200)
        self.assertEqual(pending.data["bookings"], [])

        response = self.client.post(f"/api/gsr/booking-shares/{share.pk}/accept/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], GSRBookingShare.ACCEPTED)
        self.assertEqual(len(response.data["bookings"]), 1)
        self.assertEqual(response.data["bookings"][0]["location"], self.gsr.name)
        self.assertEqual(response.data["bookings"][0]["room_name"], self.booking.room_name)
        self.assertTrue(response.data["responded_at"])

    def test_only_recipient_can_accept_or_decline(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation, inviter=self.owner, recipient=self.recipient
        )
        self.client.force_authenticate(self.other)

        accept_response = self.client.post(f"/api/gsr/booking-shares/{share.pk}/accept/")
        decline_response = self.client.post(f"/api/gsr/booking-shares/{share.pk}/decline/")

        self.assertEqual(accept_response.status_code, 404)
        self.assertEqual(decline_response.status_code, 404)
        share.refresh_from_db()
        self.assertEqual(share.status, GSRBookingShare.PENDING)

    def test_recipient_can_decline_pending_invitation(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation, inviter=self.owner, recipient=self.recipient
        )
        self.client.force_authenticate(self.recipient)

        response = self.client.post(f"/api/gsr/booking-shares/{share.pk}/decline/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], GSRBookingShare.DECLINED)
        self.assertTrue(response.data["responded_at"])

    def test_owner_can_revoke_and_recipient_loses_booking_access(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation,
            inviter=self.owner,
            recipient=self.recipient,
            status=GSRBookingShare.ACCEPTED,
        )
        self.client.force_authenticate(self.owner)

        response = self.client.delete(f"/api/gsr/booking-shares/{share.pk}/")

        self.assertEqual(response.status_code, 204)
        share.refresh_from_db()
        self.assertEqual(share.status, GSRBookingShare.REVOKED)
        self.assertTrue(share.revoked_at)

        self.client.force_authenticate(self.recipient)
        response = self.client.get(f"/api/gsr/booking-shares/{share.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["bookings"], [])

    def test_recipient_cannot_revoke_invitation(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation, inviter=self.owner, recipient=self.recipient
        )
        self.client.force_authenticate(self.recipient)

        response = self.client.delete(f"/api/gsr/booking-shares/{share.pk}/")

        self.assertEqual(response.status_code, 403)
        share.refresh_from_db()
        self.assertEqual(share.status, GSRBookingShare.PENDING)

    def test_revoked_invitation_can_be_sent_again(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation,
            inviter=self.owner,
            recipient=self.recipient,
            status=GSRBookingShare.REVOKED,
            revoked_at=timezone.now(),
        )
        self.client.force_authenticate(self.owner)

        response = self.client.post(
            "/api/gsr/booking-shares/",
            {"reservation": self.reservation.pk, "recipient": self.recipient.username},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["id"], share.pk)
        self.assertEqual(response.data["status"], GSRBookingShare.PENDING)
        self.assertIsNone(response.data["revoked_at"])
        self.assertEqual(GSRBookingShare.objects.count(), 1)

    def test_expired_or_cancelled_reservation_cannot_be_accepted(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation, inviter=self.owner, recipient=self.recipient
        )
        self.reservation.end = timezone.now() - timedelta(minutes=1)
        self.reservation.save(update_fields=["end"])
        self.client.force_authenticate(self.recipient)

        response = self.client.post(f"/api/gsr/booking-shares/{share.pk}/accept/")

        self.assertEqual(response.status_code, 400)
        share.refresh_from_db()
        self.assertEqual(share.status, GSRBookingShare.PENDING)

    def test_cancelled_booking_is_not_exposed_after_acceptance(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation,
            inviter=self.owner,
            recipient=self.recipient,
            status=GSRBookingShare.ACCEPTED,
        )
        self.booking.is_cancelled = True
        self.booking.save(update_fields=["is_cancelled"])
        self.client.force_authenticate(self.recipient)

        response = self.client.get(f"/api/gsr/booking-shares/{share.pk}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["bookings"], [])

    def test_unrelated_user_cannot_retrieve_share(self):
        share = GSRBookingShare.objects.create(
            reservation=self.reservation, inviter=self.owner, recipient=self.recipient
        )
        self.client.force_authenticate(self.other)

        response = self.client.get(f"/api/gsr/booking-shares/{share.pk}/")

        self.assertEqual(response.status_code, 404)
