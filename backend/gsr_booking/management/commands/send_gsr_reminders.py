import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from gsr_booking.models import Reservation
from user.models import NotificationSetting
from user.notifications import send_push_notifications


class Command(BaseCommand):
    help = "Sends reminders for the GSR Bookings."

    def handle(self, *args, **kwargs):

        # iterate through all reservations scheduled for the next 30 minutes
        for reservation in Reservation.objects.filter(
            is_cancelled=False,
            start__gt=timezone.now(),
            start__lte=timezone.now() + datetime.timedelta(minutes=10),
        ):
            booking = reservation.gsrbooking_set.first()
            if booking:
                title = "GSR Booking!"
                body = (
                    f"You have reserved {booking.room_name} "
                    + f"{booking.room_id} starting in 10 minutes!"
                )
                custom = {
                    "service": "GSR Booking",
                    "reservation": {
                        "room_name": booking.room_name,
                        "start": str(booking.start),
                        "end": str(booking.end),
                        "booking_id": booking.booking_id,
                    },
                }
                send_push_notifications(
                    [reservation.creator.username],
                    NotificationSetting.SERVICE_GSR_BOOKING,
                    title,
                    body,
                    custom,
                )
                reservation.reminder_sent = True
                reservation.save()

        self.stdout.write("Sent out notifications!")
