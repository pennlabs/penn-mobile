from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from gsr_booking.models import Group, GroupMembership


User = get_user_model()


class Command(BaseCommand):
    help = """
    Adds/remove users to a group.
    """

    def add_arguments(self, parser) -> None:
        parser.add_argument("usernames", type=str, help="list of pennkeys")
        parser.add_argument("group", type=str, help="group name")
        parser.add_argument("mode", type=str, help="mode of operation (add/remove/reset)")

    def handle(self, *args: Any, **kwargs: Any) -> None:
        usernames = kwargs["usernames"].split(",")
        group = kwargs["group"]
        mode = kwargs["mode"].lower()

        if mode not in ["add", "remove", "reset"]:
            self.stdout.write("Error: invalid mode")
            self.stdout.write("Options are add, remove, reset.")
            return

        if not usernames:
            self.stdout.write("Error: no users specified")
            return

        if not (group := Group.objects.filter(name=group).first()):
            self.stdout.write("Error: group not found")
            return

        users = []
        failed_users = []
        for username in usernames:
            user = User.objects.filter(username=username).first()
            if not user:
                failed_users.append(username)
            else:
                users.append(user)

        if failed_users:
            self.stdout.write("Error: users not found: " + ", ".join(failed_users))
            return

        if mode == "reset":
            group.memberships.exclude(Q(user__in=users) | Q(user=group.owner)).delete()
        elif mode == "remove":
            group.memberships.filter(Q(user__in=users) & ~Q(user=group.owner)).delete()
        if mode != "remove":
            for user in users:
                group.memberships.get_or_create(
                    user=user,
                    defaults={
                        "accepted": True,
                        "type": GroupMembership.MEMBER,
                        "pennkey_allow": True,
                    },
                )

        if mode == "reset":
            self.stdout.write("Group successfully reset!")
        elif mode == "remove":
            self.stdout.write("Members successfully removed from group!")
        else:
            self.stdout.write("Members successfully added to group!")
