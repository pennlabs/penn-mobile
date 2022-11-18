import collections
import os

from apns2.client import APNsClient
from apns2.credentials import TokenCredentials
from apns2.payload import Payload
from celery import shared_task

from dining.models import DiningMenu
from user.models import NotificationToken


# taken from the apns2 method for batch notifications
Notification = collections.namedtuple("Notification", ["token", "payload"])


def send_push_notifications(
    users, service, title, body="", custom=dict(), delay=0, is_dev=False, is_shadow=False
):
    """
    Sends push notifications.

    :param users: list of usernames to send notifications to or 'None' if to all
    :param service: service to send notifications for or 'None' if ignoring settings
    :param title: title of notification
    :param body: string body of notification
    :param custom: data passed along in notification that iOS can read
    :param delay: delay in seconds before sending notification
    :param is_dev: whether to dev user
    :param is_shadow: whether to send a shadow notification
    :return: tuple of (list of success usernames, list of failed usernames)
    """

    # collect available usernames & their respective device tokens
    token_objects = get_tokens(users, service)
    if not token_objects:
        return [], users
    success_users, tokens = zip(*token_objects)
    
    # send notifications
    args = (tokens, title, body, custom, service, is_dev, is_shadow)
    if delay:
        send_delayed_notifications(args, delay)
    else:
        send_immediate_notifications(*args)

    if not users:  # if to all users, can't be any failed pennkeys
        return success_users, []
    failed_users = list(set(users) - set(success_users))
    return success_users, failed_users


def get_tokens(users=None, service=None):
    """Returns list of token objects (with username & token value) for specified users"""

    token_objs = NotificationToken.objects.select_related("user").filter(
        kind=NotificationToken.KIND_IOS  # NOTE: until Android implementation
    )
    if users:
        token_objs = token_objs.filter(user__username__in=users)
    if service:
        token_objs = token_objs.filter(
            notificationsetting__service=service, notificationsetting__enabled=True
        )
    return token_objs.exclude(token="").values_list("user__username", "token")


@shared_task(name="notifications.send_immediate_notifications")
def send_immediate_notifications(tokens, title, body, custom, category, is_dev, is_shadow):
    client = get_client(is_dev)
    if is_shadow:
        payload = Payload(
            content_available=True, mutable_content=True, custom=custom, category=category
        )
    else:
        alert = {"title": title, "body": body}
        payload = Payload(
            alert=alert,
            sound="default",
            badge=0,
            mutable_content=True,
            custom=custom,
            category=category,
        )
    topic = "org.pennlabs.PennMobile" + (".dev" if is_dev else "")

    if len(tokens) > 1:
        notifications = [Notification(token, payload) for token in tokens]
        client.send_notification_batch(notifications=notifications, topic=topic)
    else:
        client.send_notification(tokens[0], payload, topic)


def send_delayed_notifications(args, delay):
    send_immediate_notifications.apply_async(args, countdown=delay)


def get_auth_key_path():
    return os.environ.get(
        "IOS_KEY_PATH",  # for dev purposes
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ios_key.p8"),
    )


def get_client(is_dev):
    """Creates and returns APNsClient based on iOS credentials"""

    auth_key_path = get_auth_key_path()
    auth_key_id = "2VX9TC37TB"
    team_id = "VU59R57FGM"
    token_credentials = TokenCredentials(
        auth_key_path=auth_key_path, auth_key_id=auth_key_id, team_id=team_id
    )
    client = APNsClient(credentials=token_credentials, use_sandbox=is_dev)
    return client
