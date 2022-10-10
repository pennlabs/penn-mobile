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
        parser.add_argument("message", type=str, help="JSON-formatted message to send")

        # optional argument
        parser.add_argument("--usernames", type=str, help="list of usernames")
        parser.add_argument("--is_dev", type=str, default="no")

    def handle(self, *args, **kwargs):
        send_to_all = kwargs["send_to_all"].lower() == "yes"
        message = json.loads(kwargs["message"])
        names = kwargs["usernames"]
        # NOTE: uncomment once fixed
        # is_dev = kwargs["is_dev"].lower() == "yes"

        # get list of targeted users if not to everyone
        if not send_to_all:
            usernames = names.split(",") if "," in names else [names]
        else:
            usernames = None

        # send notifications
        _, failed_users = send_push_notifications(usernames, None, None, message, is_shadow=True)

        if len(failed_users) > 0:
            self.stdout.write("Unavailable token(s) for " + ", ".join(failed_users) + ".")
        self.stdout.write("Notifications sent out!")
