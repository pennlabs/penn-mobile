import collections
import os

from apns2.client import APNsClient
from apns2.credentials import TokenCredentials
from apns2.payload import Payload


# taken from the apns2 method for batch notifications
Notification = collections.namedtuple("Notification", ["token", "payload"])


def send_push_notification(token, title, body, isDev=False):
    client = get_client(isDev)
    alert = {"title": title, "body": body}
    payload = Payload(alert=alert, sound="default", badge=0)
    topic = "org.pennlabs.PennMobile"
    client.send_notification(token.token, payload, topic)


def send_push_notification_batch(tokens, title, body, isDev=False):
    client = get_client(isDev)
    alert = {"title": title, "body": body}
    payload = Payload(alert=alert, sound="default", badge=0)
    notifications = [Notification(token.token, payload) for token in tokens]
    topic = "org.pennlabs.PennMobile"
    client.send_notification_batch(notifications=notifications, topic=topic)


def get_client(isDev):
    auth_key_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ios_key.p8"
    )
    auth_key_id = "443RV92X4F"
    team_id = "VU59R57FGM"
    token_credentials = TokenCredentials(
        auth_key_path=auth_key_path, auth_key_id=auth_key_id, team_id=team_id
    )
    client = APNsClient(credentials=token_credentials, use_sandbox=isDev)
    return client
