from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from gsr_booking.api_wrapper import PennGroupsGSRBooker, WhartonGSRBooker
from gsr_booking.models import Group, GroupMembership


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Add users to the Penn Labs group as regular members. Checks Wharton status automatically."
    )

    def handle(self, *args, **options):
        try:
            group = Group.objects.get(name="Penn Labs")
        except Group.DoesNotExist:
            raise CommandError('Group "Penn Labs" does not exist!')

        users = []
        wharton_statuses = []
        seas_statuses = []

        input_count = int(input("How many users would you like to add? "))
        if input_count <= 0:
            self.stdout.write("No users to add. Exiting.")
            return

        for _ in range(input_count):
            pennkey = input("Enter the PennKey of the user to add: ").strip()
            try:
                user = User.objects.get(username=pennkey)
            except User.DoesNotExist:
                self.stdout.write(f"User with PennKey {pennkey} does not exist. Skipping.")
                continue
            users.append(user)
            is_wharton = WhartonGSRBooker.is_wharton(user)
            wharton_statuses.append(is_wharton)
            is_seas = PennGroupsGSRBooker.is_seas(user)
            seas_statuses.append(is_seas)

        # confirm with the admin before proceeding
        self.stdout.write("The following users will be added to the Penn Labs group:")
        for user, is_wharton in zip(users, wharton_statuses):
            status_parts = []
            if is_wharton:
                status_parts.append("Wharton")
            if is_seas:
                status_parts.append("SEAS")
            if not status_parts:
                status_parts.append("Regular")
            status = " + ".join(status_parts)
            self.stdout.write(f"- {user.username} ({status})")
        confirm = input("Type 'yes' to confirm and proceed: ").strip().lower()
        if confirm != "yes":
            self.stdout.write("Aborted.")
            return
        for user, is_wharton in zip(users, wharton_statuses):
            membership, created = GroupMembership.objects.get_or_create(
                user=user,
                group=group,
                defaults={
                    "type": GroupMembership.MEMBER,
                    "accepted": True,
                    "pennkey_allow": True,
                    "is_wharton": is_wharton,
                    "is_seas": is_seas,
                },
            )
            if not created:
                # Update existing membership to ensure it has correct settings
                membership.type = GroupMembership.MEMBER
                membership.accepted = True
                membership.pennkey_allow = True
                membership.is_wharton = is_wharton
                membership.is_seas = is_seas
                membership.save()
                self.stdout.write(f"Updated existing membership for {user.username}")
            else:
                self.stdout.write(f"Created new membership for {user.username}")
