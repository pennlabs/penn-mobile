from django.core.management.base import BaseCommand

from gsr_booking.models import GroupMembership


groups = [
    "a-d",  # 4107
    "e-j",  # 3674
    "k-n",  # 3583
    "o-s",  # 2852
    "t-z",  # 2103
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("group", type=int)

    def handle(self, *args, **kwargs):
        group = kwargs["group"]
        if group not in range(1, 6):
            self.stdout.write("Error: fraction must be between 1 and 5")
            return
        GroupMembership.objects.filter(
            is_wharton=False, user__username__iregex=rf"^[{groups[group-1]}]"
        ).update(is_wharton=None)
        self.stdout.write("Successfully reset Wharton caching")
