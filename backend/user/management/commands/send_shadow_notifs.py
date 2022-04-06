import json

from django.core.management.base import BaseCommand

from user.models import NotificationToken
from user.notifications import send_shadow_push_notif_batch


class Command(BaseCommand):
    help = """
    Sends shadow notifs to all or targeted users.
    -
    Example Input:
    Send to all (yes/no)? No
    Target users (comma-delimitted): pennkey1,pennkey2,pennkey3
    isDev (yes/no)? No
    JSON-formatted message: {"a":"b","c":{"d":"e"},"f":["g","h"]}
    """

    def handle(self, *args, **kwargs):
        send_to_all = input("Send to all (yes/no)? ").lower() == "yes"
        # get list of targeted users if not to everyone
        if not send_to_all:
            usernames = input("Target users (comma-delimitted): ").split(",")
        isDev = input("isDev (yes/no)? ").lower() == "yes"
        message = json.loads(input("JSON-formatted message: "))

        # get list of tokens
        if send_to_all:
            tokens = NotificationToken.objects.exclude(token="")
        else:
            tokens = (
                NotificationToken.objects.select_related("user")
                .filter(
                    kind=NotificationToken.KIND_IOS,  # NOTE: until Android implementation
                    user__username__in=usernames,
                )
                .exclude(token="")
            )

        # send shadow notifications
        send_shadow_push_notif_batch(tokens=tokens, body=message, isDev=isDev)

        if not send_to_all:
            failed_users = list(set(usernames) - set([token.user.username for token in tokens]))
            # output list of targeted users without tokens if such a list exists
            if len(failed_users) > 0:
                self.stdout.write("Unavailable token(s) for " + ", ".join(failed_users) + ".")
        self.stdout.write("Notifications sent out!")
