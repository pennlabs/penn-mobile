from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.timezone import localtime

from gsr_booking.models import Group, GroupMembership, GSRBooking, Reservation


class Command(BaseCommand):
    help = "Provides visiblity data for Penn Labs Group GSRs."

    def handle(self, *args, **kwargs):
        group = Group.objects.get(name="Penn Labs")
        reservations = Reservation.objects.filter(
            group=group, is_cancelled=False, start__gte=timezone.now()
        )
        wharton_members = GroupMembership.objects.filter(group=group, is_wharton=True)
        total_time = wharton_members.count() * 90
        time_used = 0
        print("| Owner:\t | Taken From:\t | Location:\t | Time Start:\t\t | Duration:")
        for res in reservations:
            bookings = GSRBooking.objects.filter(reservation=res, is_cancelled=False)
            for booking in bookings:
                duration = (booking.end - booking.start).total_seconds() / 60
                start = localtime(booking.start).strftime("%m/%d/%Y @ %H:%M")
                message = (
                    f"| {res.creator.username}\t| {booking.user.username}\t| "
                    f"{booking.gsr.name}\t| {str(start)}\t| {int(duration)}"
                )
                print(message)
                if booking.gsr.gid == 1 or booking.gsr.gid == 6:
                    time_used += (booking.end.timestamp() - booking.start.timestamp()) / 60
        print(f"Total Credits Used: {int(time_used)}")
        print(f"Total Wharton Credits: {total_time}")
