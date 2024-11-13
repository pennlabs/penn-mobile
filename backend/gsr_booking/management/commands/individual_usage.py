from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from gsr_booking.models import Group, GSRBooking


class Command(BaseCommand):
    help = "Provides usage stats for a given user."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("pennkey", type=str, help="Pennkey of user to check")

    def handle(self, *args: Any, **kwargs: Any) -> None:
        pennkey = kwargs["pennkey"]
        groups = Group.objects.filter(memberships__user__username=pennkey)
        bookings = GSRBooking.objects.filter(
            reservation__creator__username=pennkey,
            reservation__is_cancelled=False,
            reservation__end__lte=timezone.now(),
            is_cancelled=False,
        )

        for group in groups:
            print(f'Usage for group "{group.name}":')
            group_bookings = bookings.filter(reservation__group=group)
            total_time = sum(
                (booking.end - booking.start).total_seconds() / 60 for booking in group_bookings
            )
            print(f"Total Credits Used: {int(total_time)}")
            print()
