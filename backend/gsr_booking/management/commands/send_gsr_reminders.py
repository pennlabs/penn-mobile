import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from gsr_booking.models import Reservation
from user.models import SERVICE_GSR_BOOKING, NotificationToken
from user.notifications import send_push_notif


class Command(BaseCommand):
    help = "Sends reminders for the GSR Bookings."

    def handle(self, *args, **kwargs):
        # iterate through all reservations scheduled for the next 30 minutes
        for reservation in Reservation.objects.filter(
            is_cancelled=False,
            start__gt=timezone.now(),
            start__lte=timezone.now() + datetime.timedelta(minutes=10),
        ):
            # NOTE: only iOS for now, change when Android gets set up
            token = (
                NotificationToken.objects.filter(
                    user=reservation.creator, kind=NotificationToken.KIND_IOS
                )
                .exclude(token="")
                .first()
            )

            if token:
                # skip user if their setting is disabled for GSR Notifs
                setting = token.objects.filter(service=SERVICE_GSR_BOOKING).first()
                if not setting or not setting.enabled:
                    continue

                booking = reservation.gsrbooking_set.first()
                if booking:
                    title = "GSR Booking!"
                    body = (
                        f"You have reserved {booking.room_name} "
                        + f"{booking.room_id} starting in 10 minutes!"
                    )
                    send_push_notif(token.token, title, body)

        self.stdout.write("Sent out notifications!")
