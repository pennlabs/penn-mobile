import os

from apns2.client import APNsClient
from apns2.credientials import TokenCredentials
from apns2.payload import Payload


def send_push_notification(token, title, body, isDev=False):
    client = get_client(isDev)
    alert = {"title": title, "body": body}
    payload = Payload(alert=alert, sound="default", badge=0)
    topic = "org.pennlabs.PennMobile"
    client.send_notification(token, payload, topic)


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
