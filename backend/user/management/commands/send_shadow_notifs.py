import json

from django.core.management.base import BaseCommand

from user.models import NotificationToken
from user.notifications import send_shadow_push_notif_batch


class Command(BaseCommand):
    help = """
    Sends shadow notifs to all or targeted users.
    ——
    Example:
    <>
    send_to_all: no
    <>
    message: '{"a":"b","c":{"d":"e"},"f":["g","h"]}'
    (Note: must enclose message in single quotes)
    <>
    (Optional) usernames: pennkey1,pennkey2,pennkey3
    (Note: must be comma-delimitted)
    <>
    (Optional) isDev: no
    <>
    """

    def add_arguments(self, parser):
        parser.add_argument("send_to_all", type=str, help="whether to send to all")
        parser.add_argument("message", type=str, help="JSON-formatted message to send")

        # optional argument
        parser.add_argument("--usernames", type=str, help="list of usernames")
        parser.add_argument("--isDev", type=str, default="no")

    def handle(self, *args, **kwargs):
        send_to_all = kwargs["send_to_all"].lower() == "yes"

        # get list of targeted users if not to everyone
        if not send_to_all:
            names = kwargs["usernames"]
            usernames = names.split(",") if "," in names else [names]

        isDev = kwargs["isDev"].lower() == "yes"
        message = json.loads(kwargs["message"])

        # get list of tokens
        if send_to_all:
            tokens = NotificationToken.objects.exclude(token="").values_list("token", flat=True)
        else:
            tokens = (
                NotificationToken.objects.select_related("user")
                .filter(
                    kind=NotificationToken.KIND_IOS,  # NOTE: until Android implementation
                    user__username__in=usernames,
                )
                .exclude(token="")
                .values_list("user__username", "token")
            )
            # unpack list of tuples
            success_users, tokens = zip(*tokens)
            failed_users = list(set(usernames) - set(success_users))
            
            # output list of targeted users without tokens if such a list exists
            if len(failed_users) > 0:
                self.stdout.write("Unavailable token(s) for " + ", ".join(failed_users) + ".")

        # send shadow notifications
        send_shadow_push_notif_batch(tokens=tokens, body=message, isDev=isDev)

        self.stdout.write("Notifications sent out!")
