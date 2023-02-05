import json

from django.core.management.base import BaseCommand

from user.notifications import send_push_notifications


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
        parser.add_argument("custom", type=str, help="JSON-formatted message to send")

        # optional argument
        parser.add_argument("--users", type=str, help="list of pennkeys")
        parser.add_argument("--delay", type=int, default=0)
        parser.add_argument("--is_dev", type=str, default="no")

    def handle(self, *args, **kwargs):
        send_to_all = kwargs["send_to_all"].lower() == "yes"
        custom = json.loads(kwargs["custom"])
        names = kwargs["users"]
        delay = kwargs["delay"]
        is_dev = kwargs["is_dev"].lower() == "yes"

        # get list of targeted users if not to everyone
        if not send_to_all:
            users = names.split(",") if "," in names else [names]
        else:
            users = None

        # send notifications
        _, failed_users = send_push_notifications(
            users, None, None, None, custom, delay, is_dev, is_shadow=True
        )

        if len(failed_users) > 0:
            self.stdout.write("Unavailable token(s) for " + ", ".join(failed_users) + ".")
        self.stdout.write("Notifications sent out!")
