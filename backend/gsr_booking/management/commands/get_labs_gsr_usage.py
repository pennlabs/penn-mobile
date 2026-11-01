from collections import defaultdict
from datetime import datetime, time, timedelta
from datetime import timezone as datetime_timezone

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from gsr_booking.models import Group, GSRBooking


class Command(BaseCommand):
    help = (
        "Show Penn Labs' top 10 GSR users and total booked hours per day and overall. "
        "Use --lid to filter by GSR.lid; otherwise includes all GSR locations. "
        "Includes today (including later today), using the configured local timezone. "
        "Usage is attributed to reservation creators, not credit owners."
    )

    def add_arguments(self, parser):
        parser.add_argument("days", type=int, help="Number of calendar days, including today")
        parser.add_argument("--lid", help="GSR location ID (GSR.lid), e.g. JMHH")

    def handle(self, *args, **options):
        days = options["days"]
        if days <= 0:
            raise CommandError("days must be a positive integer.")

        local_timezone = timezone.get_default_timezone()
        today = timezone.localdate(timezone.now(), timezone=local_timezone)
        try:
            first_day = today - timedelta(days=days - 1)
        except OverflowError as exc:
            raise CommandError("days exceeds the supported date range.") from exc

        def midnight_utc(day):
            return datetime.combine(day, time.min, tzinfo=local_timezone).astimezone(
                datetime_timezone.utc
            )

        window_start = midnight_utc(first_day)
        window_end = midnight_utc(today + timedelta(days=1))

        try:
            group = Group.objects.get(name="Penn Labs")
        except Group.DoesNotExist as exc:
            raise CommandError('Group "Penn Labs" was not found.') from exc
        except Group.MultipleObjectsReturned as exc:
            raise CommandError('Multiple groups named "Penn Labs" were found.') from exc

        bookings = GSRBooking.objects.filter(
            reservation__group=group,
            reservation__is_cancelled=False,
            is_cancelled=False,
            start__lt=window_end,
            end__gt=window_start,
        )
        lid = options["lid"]
        if lid is not None:
            bookings = bookings.filter(gsr__lid=lid)
        bookings = bookings.values_list(
            "reservation__creator_id", "reservation__creator__username", "start", "end"
        )

        daily_usage = defaultdict(lambda: defaultdict(float))
        total_usage = defaultdict(float)
        usernames = {}
        for creator_id, username, start, end in bookings.iterator():
            usernames[creator_id] = username
            # Work in UTC so elapsed hours remain correct across DST transitions.
            cursor = max(start.astimezone(datetime_timezone.utc), window_start)
            end = min(end.astimezone(datetime_timezone.utc), window_end)
            while cursor < end:
                day = cursor.astimezone(local_timezone).date()
                segment_end = min(end, midnight_utc(day + timedelta(days=1)))
                seconds = (segment_end - cursor).total_seconds()
                daily_usage[day][creator_id] += seconds
                total_usage[creator_id] += seconds
                cursor = segment_end

        self.stdout.write(
            f"Penn Labs GSR usage: {first_day} through {today} ({local_timezone})\n"
            f"Locations: {'All GSRs' if lid is None else f'lid={lid}'}\n"
            "Booked hours by reservation creator; includes bookings later today."
        )
        for offset in range(days):
            day = today - timedelta(days=offset)
            usage = daily_usage[day]
            self.stdout.write(f"\n{day} — Top 10 users")
            self.write_ranking(usage, usernames)
            self.stdout.write(f"Daily total (all users): {sum(usage.values()) / 3600:.2f} hours")

        self.stdout.write("\nPeriod — Top 10 users")
        self.write_ranking(total_usage, usernames)
        self.stdout.write(f"Grand total (all users): {sum(total_usage.values()) / 3600:.2f} hours")

    def write_ranking(self, usage, usernames):
        if not usage:
            self.stdout.write("No bookings.")
            return

        self.stdout.write("Rank\tUsername\tHours")
        ranked_users = sorted(usage, key=lambda user_id: (-usage[user_id], usernames[user_id]))
        for rank, user_id in enumerate(ranked_users[:10], start=1):
            self.stdout.write(f"{rank}\t{usernames[user_id]}\t{usage[user_id] / 3600:.2f}")
