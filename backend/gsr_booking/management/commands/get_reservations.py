from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from gsr_booking.models import Group, Reservation


User = get_user_model()


class Command(BaseCommand):
    help = """
    Get number of reservations using GSR bookings.

    Defaulted to current number. Use --start or --end to specify date range.

    --group     flag to specify group
    --start     flag to specify start date; expected format: YYYY-MM-DD
    --end       flag to specify end date; expected format: YYYY-MM-DD
    --current   flag to specify current reservations
    --time      flag to specify total time of reservations
    --user      flag to specify to get number of unique users

    Note: --start/--end and --current are mutually exclusive
    """

    def add_arguments(self, parser):
        # optional flags
        parser.add_argument("--group", type=str, default=None)
        parser.add_argument("--start", type=str, default=None)
        parser.add_argument("--end", type=str, default=None)
        parser.add_argument("--current", type=bool, default=False)
        parser.add_argument("--time", type=bool, default=False)
        parser.add_argument("--user", type=bool, default=False)

    def handle(self, *args, **kwargs):
        group = kwargs["group"]
        start = kwargs["start"]
        end = kwargs["end"]
        current = kwargs["current"]
        time = kwargs["time"]
        user = kwargs["user"]

        if start and not (start := self.__convert_date(start)):
            self.stdout.write("Error: invalid start date format")
            return
        if end and not (end := self.__convert_date(end)):
            self.stdout.write("Error: invalid end date format")
            return

        reservation_filter = Q()
        if current:
            reservation_filter &= Q(start__lte=datetime.now()) & Q(end__gte=datetime.now())
        else:
            if start:
                reservation_filter &= Q(start__gte=start)
            if end:
                reservation_filter &= Q(end__lte=end)

        if group:
            if not (group := Group.objects.filter(name=group).first()):
                self.stdout.write("Error: group not found")
                return
            reservations = group.reservations.filter(reservation_filter)
        else:
            reservations = Reservation.objects.filter(reservation_filter)

        if time:
            total_time = (
                sum(
                    (reservation.end - reservation.start).total_seconds()
                    for reservation in reservations
                )
                / 3600
            )
            self.stdout.write(f"Total time: {total_time}")
        if user:
            users = reservations.values_list("creator", flat=True).distinct()
            self.stdout.write(f"Number of unique users: {users.count()}")

        self.stdout.write(f"Number of reservations: {reservations.count()}")

    def __convert_date(self, date_str):
        """
        Converts string in format YYYY-MM-DD to datetime object.
        Returns None if string is not in correct format.

        :param date_str: string in format YYYY-MM-DD
        :return: datetime object
        """

        try:
            return timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        except ValueError:
            return None
