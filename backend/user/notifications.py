import collections
import os
import sys


# Monkey Patch for apn2 errors, referenced from:
# https://github.com/jazzband/django-push-notifications/issues/622
if sys.version_info.major >= 3 and sys.version_info.minor >= 10:
    """
    The apns2 package is throwing errors because some aliases in collections
    were removed in 3.10. Specifically, the error is coming from a dependency
    of apns2 named hyper.
    """
    from collections import abc

    collections.Iterable = abc.Iterable
    collections.Mapping = abc.Mapping
    collections.MutableSet = abc.MutableSet
    collections.MutableMapping = abc.MutableMapping

from apns2.client import APNsClient
from apns2.credentials import TokenCredentials
from apns2.payload import Payload
from celery import shared_task

from user.models import NotificationToken


# taken from the apns2 method for batch notifications
Notification = collections.namedtuple("Notification", ["token", "payload"])


def send_push_notifications(users, service, title, body, delay=0, is_dev=False, is_shadow=False):
    """
    Sends push notifications.

    :param users: list of usernames to send notifications to or 'None' if to all
    :param service: service to send notifications for or 'None' if ignoring settings
    :param title: title of notification
    :param body: body of notification
    :param delay: delay in seconds before sending notification
    :param isShadow: whether to send a shadow notification
    :return: tuple of (list of success usernames, list of failed usernames)
    """

    # collect available usernames & their respective device tokens
    token_objects = get_tokens(users, service)
    if not token_objects:
        return [], users
    success_users, tokens = zip(*token_objects)

    # send notifications
    if delay:
        send_delayed_notifications(tokens, title, body, service, is_dev, is_shadow, delay)
    else:
        send_immediate_notifications(tokens, title, body, service, is_dev, is_shadow)

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
def send_immediate_notifications(tokens, title, body, category, is_dev, is_shadow):
    client = get_client(is_dev)
    if is_shadow:
        payload = Payload(
            content_available=True, custom=body, mutable_content=True, category=category
        )
    else:
        alert = {"title": title, "body": body}
        payload = Payload(
            alert=alert, sound="default", badge=0, mutable_content=True, category=category
        )
    topic = "org.pennlabs.PennMobile" + (".dev" if is_dev else "")

    if len(tokens) > 1:
        notifications = [Notification(token, payload) for token in tokens]
        client.send_notification_batch(notifications=notifications, topic=topic)
    else:
        client.send_notification(tokens[0], payload, topic)


def send_delayed_notifications(tokens, title, body, category, is_dev, is_shadow, delay):
    send_immediate_notifications.apply_async(
        (tokens, title, body, category, is_dev, is_shadow), countdown=delay
    )


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
