import asyncio

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from gsr_booking.api_wrapper import WhartonBookingWrapper
from gsr_booking.models import GroupMembership


class Command(BaseCommand):
    help = "Updates Wharton privilege status for all users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--concurrency",
            type=int,
            default=20,
            help="Max concurrent API calls (default: 20).",
        )

    def handle(self, *args, **kwargs):
        asyncio.run(self.ahandle(**kwargs))

    async def ahandle(self, **kwargs):
        max_concurrency = kwargs["concurrency"]
        usernames = await asyncio.to_thread(
            lambda: list(
                GroupMembership.objects.values_list("user__username", flat=True).distinct()
            )
        )

        self.stdout.write(f"Checking {len(usernames)} users (concurrency={max_concurrency})...")

        semaphore = asyncio.Semaphore(max_concurrency)
        updated_count = 0

        async def process_user(username: str) -> int:
            async with semaphore:
                wrapper = WhartonBookingWrapper()
                user = await asyncio.to_thread(get_user_model().objects.get, username=username)
                is_wharton = await asyncio.to_thread(wrapper.is_wharton, user)

                memberships = await asyncio.to_thread(
                    lambda: list(GroupMembership.objects.filter(user__username=username))
                )

                count = 0
                for membership in memberships:
                    if membership.is_wharton != is_wharton:
                        membership.is_wharton = is_wharton
                        await asyncio.to_thread(membership.save)
                        status = "now" if is_wharton else "no longer"
                        self.stdout.write(f"User {user} is {status} a Wharton user.")
                        count += 1
                return count

        results = await asyncio.gather(
            *(process_user(u) for u in usernames),
            return_exceptions=True,
        )

        for username, result in zip(usernames, results):
            if isinstance(result, Exception):
                self.stderr.write(f"Error processing {username}: {result}")
            else:
                updated_count += result

        self.stdout.write(f"Done updating Wharton statuses. Updated: {updated_count} users.")
