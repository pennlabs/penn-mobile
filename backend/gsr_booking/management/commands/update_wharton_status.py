from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from gsr_booking.api_wrapper import WhartonBookingWrapper
from gsr_booking.models import GroupMembership


class Command(BaseCommand):
    help = "Updates Wharton privelige status for all users."

    def handle(self, *args, **kwargs):
        users = GroupMembership.objects.values_list("user__username", flat=True).distinct()
        print(f"Checking {len(users)} users...")
        for username in users:
            user = get_user_model().objects.get(username=username)
            is_wharton = WhartonBookingWrapper().is_wharton(user)
            memberships = GroupMembership.objects.filter(user__username=user)
            for membership in memberships:
                if membership.is_wharton != is_wharton:
                    membership.is_wharton = is_wharton
                    membership.save()
                    status = "now" if is_wharton else "no longer"
                    print(f"User {user} is {status} a Wharton user.")
        print("Done updating Wharton statuses.")
