from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from gsr_booking.models import Group, GroupMembership


User = get_user_model()


class Command(BaseCommand):
    help = """
    Adds/remove users to a group.

    --remove flag for users to be removed from the group
    --reset flag to set group to be all users specified in command

    Note: --remove and --reset are mutually exclusive
    """

    def add_arguments(self, parser):
        parser.add_argument("usernames", type=str, help="list of pennkeys")
        parser.add_argument("group", type=str, help="group name")

        # optional flags
        parser.add_argument("--remove", type=bool, default=False)
        parser.add_argument("--reset", type=bool, default=False)

    def handle(self, *args, **kwargs):
        usernames = kwargs["usernames"].split(",")
        group = kwargs["group"]
        remove = kwargs["remove"]
        reset = kwargs["reset"]

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

        if reset:
            group.memberships.exclude(Q(user__in=users) | Q(user=group.owner)).delete()
        if reset or not remove:
            for user in users:
                group.memberships.get_or_create(
                    user=user,
                    defaults={
                        "accepted": True,
                        "type": GroupMembership.MEMBER,
                        "pennkey_allow": True,
                    },
                )
        elif remove:
            group.memberships.filter(user__in=users).delete()

        if reset:
            self.stdout.write("Group successfully reset!")
        elif remove:
            self.stdout.write("Members successfully removed from group!")
        else:
            self.stdout.write("Members successfully added to group!")
