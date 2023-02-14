from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from gsr_booking.models import Group, GroupMembership


User = get_user_model()


class Command(BaseCommand):
    help = """
    Adds users to a group.
    --reset flag
    Sets all group members to be the users specified in the command.
    """

    def add_arguments(self, parser):
        parser.add_argument("usernames", type=str, help="list of pennkeys")
        parser.add_argument("group", type=str, help="group name")

        # optional flag to set group to be all users
        parser.add_argument("--reset", type=bool, default=False)

    def handle(self, *args, **kwargs):
        usernames = kwargs["usernames"].split(",")
        group = kwargs["group"]
        reset = kwargs["reset"]

        if not (group := Group.objects.filter(name=group).first()):
            self.stdout.write("Group not found.")
            return

        users = []
        failed_users = []
        for username in usernames:
            user = User.objects.filter(username=username).first()
            if not user:
                failed_users.append(username)
            else:
                users.append(user)

        if reset and failed_users:
            self.stdout.write("Failed users: " + ", ".join(failed_users))
            self.stdout.write("Exiting now...")
            return

        if reset:
            group.memberships.exclude(
                            Q(user__in=users) | Q(user=group.owner)
                        ).delete()
        for user in users:
            group.memberships.get_or_create(
                user=user,
                defaults={"accepted": True, "type": GroupMembership.MEMBER, "pennkey_allow": True},
            )

        if failed_users:
            self.stdout.write("Failed users: " + ", ".join(failed_users))
        if users:
            self.stdout.write("Members added to group!")