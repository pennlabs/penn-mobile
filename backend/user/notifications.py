import collections
import os

from apns2.client import APNsClient
from apns2.credentials import TokenCredentials
from apns2.payload import Payload
from celery import shared_task

from user.models import NotificationToken


# taken from the apns2 method for batch notifications
Notification = collections.namedtuple("Notification", ["token", "payload"])


def send_push_notifications(
    usernames, service, title, body, delay=0, isShadow=False
):
    """
    Sends push notifications.

    :param usernames: list of usernames to send notifications to or 'None' if to all
    :param service: service to send notifications for or 'None' if ignoring settings
    :param title: title of notification
    :param body: body of notification
    :param delay: delay in seconds before sending notification
    :param isShadow: whether to send a shadow notification
    :return: tuple of (list of success usernames, list of failed usernames)
    """

    token_objects = get_tokens(usernames, service)
    if not token_objects:
        return [], usernames

    success_users, tokens = zip(*token_objects)
    send_notifications(tokens, title, body, delay, isDev=False, isShadow=isShadow)
    if not usernames:  # if to all users, can't be any failed pennkeys
        return success_users, []
    failed_users = list(set(usernames) - set(success_users))
    return success_users, failed_users


def get_tokens(usernames=None, service=None):
    """Returns list of token objects (with username & token value) for specified users"""

    token_objs = NotificationToken.objects.select_related("user").filter(
        kind=NotificationToken.KIND_IOS  # NOTE: until Android implementation
    )
    if usernames:
        token_objs = token_objs.filter(user__username__in=usernames)
    if service:
        token_objs = token_objs.filter(notificationsetting__service=service, notificationsetting__enabled=True)
    return token_objs.exclude(token="").values_list("user__username", "token")


def send_notifications(tokens, title, body, delay, isDev, isShadow):
    """Formulates and pushes notifications to APNs"""

    client = get_client(isDev)
    alert = {"title": title, "body": body}
    if isShadow:
        payload = Payload(content_available=True, custom=body)
    else:
        payload = Payload(alert=alert, sound="default", badge=0)
    topic = "org.pennlabs.PennMobile" + (".dev" if isDev else "")

    if delay:
        send_delayed_notifications(client, tokens, payload, topic, delay)
    else:
        send_immediate_notifications(client, tokens, payload, topic)


def send_immediate_notifications(client, tokens, payload, topic):
    if len(tokens) > 1:
        notifications = [Notification(token, payload) for token in tokens]
        client.send_notification_batch(notifications=notifications, topic=topic)
    else:
        client.send_notification(tokens[0], payload, topic)


@shared_task(name="notifications.send_delayed_notifications")
def send_delayed_notifications(client, tokens, payload, topic, delay):
    send_immediate_notifications.apply_async(args=[client, tokens, payload, topic], countdown=delay)


def get_client(isDev):
    """Creates and returns APNsClient based on iOS credentials"""

    auth_key_path = os.environ.get(
        "IOS_KEY_PATH",  # for dev purposes
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ios_key.p8"),
    )
    auth_key_id = "443RV92X4F"
    team_id = "VU59R57FGM"
    token_credentials = TokenCredentials(
        auth_key_path=auth_key_path, auth_key_id=auth_key_id, team_id=team_id
    )
    client = APNsClient(credentials=token_credentials, use_sandbox=isDev)
    return client
