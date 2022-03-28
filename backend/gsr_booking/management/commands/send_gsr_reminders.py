import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from gsr_booking.models import Reservation
from user.models import SERVICE_GSR_BOOKING, NotificationToken
from user.notifications import send_push_notification


class Command(BaseCommand):
    help = "Sends reminders for the GSR Bookings."

    def handle(self, *args, **kwargs):
        for reservation in Reservation.objects.filter(
            start__gt=timezone.now(), start__lte=timezone.now() + datetime.timedelta(minutes=30)
        ):
            if reservation.is_cancelled:
                continue

            creator = reservation.creator

            # NOTE: only iOS for now, change when Android gets set up
            token = NotificationToken.objects.filter(
                user=creator, kind=NotificationToken.KIND_IOS
            ).first()

            if token:
                # skip user if their setting = disabled for GSR Notifs
                setting = token.objects.filter(service=SERVICE_GSR_BOOKING).first()
                if setting and not setting.enabled:
                    continue

                booking = reservation.gsrbooking_set.first()
                title = "GSR Booking!"
                body = (
                    f"Upcoming GSR Reservation in {booking.room_name} {booking.room_id} "
                    + "in 30 minutes!"
                    if booking
                    else "Upcoming GSR Reservation in 30 minutes!"
                )

                send_push_notification(token.token, title, body)

        self.stdout.write("Sent out notifications!")
