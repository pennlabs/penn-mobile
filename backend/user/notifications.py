import collections
import os
import sys
from abc import ABC, abstractmethod

import firebase_admin
from firebase_admin import credentials, messaging


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

from apns2.client import APNsClient, Notification
from apns2.payload import Payload
from celery import shared_task


class NotificationWrapper(ABC):
    def send_notification(self, tokens, title, body):
        self.send_payload(tokens, self.create_payload(title, body))

    def send_shadow_notification(self, tokens, body):
        self.send_payload(tokens, self.create_shadow_payload(body))

    def send_payload(self, tokens, payload):
        if len(tokens) == 0:
            raise ValueError("No tokens provided")
        elif len(tokens) > 1:
            self.send_many_notifications(tokens, payload)
        else:
            self.send_one_notification(tokens[0], payload)

    @abstractmethod
    def create_payload(self, title, body):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def create_shadow_payload(self, body):
        raise NotImplementedError

    @abstractmethod
    def send_many_notifications(self, tokens, payload):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def send_one_notification(self, token, payload):
        raise NotImplementedError


class AndroidNotificationWrapper(NotificationWrapper):
    def __init__(self):
        try:
            server_key = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "penn-mobile-android-firebase-adminsdk-u9rki-c83fb20713.json",
            )
            cred = credentials.Certificate(server_key)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Notifications Error: Failed to initialize Firebase client: {e}")

    def create_payload(self, title, body):
        return {"notification": messaging.Notification(title=title, body=body)}

    def create_shadow_payload(self, body):
        return {"data": body}

    def send_many_notifications(self, tokens, payload):
        message = messaging.MulticastMessage(tokens=tokens, **payload)
        messaging.send_each_for_multicast(message)
        # TODO: log response errors

    def send_one_notification(self, token, payload):
        message = messaging.Message(token=token, **payload)
        messaging.send(message)


class IOSNotificationWrapper(NotificationWrapper):
    @staticmethod
    def get_client(is_dev):
        auth_key_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            f"apns-{'dev' if is_dev else 'prod'}.pem",
        )
        return APNsClient(credentials=auth_key_path, use_sandbox=is_dev)

    def __init__(self, is_dev=False):
        try:
            self.client = self.get_client(is_dev)
            self.topic = "org.pennlabs.PennMobile" + (".dev" if is_dev else "")
        except Exception as e:
            print(f"Notifications Error: Failed to initialize APNs client: {e}")

    def create_payload(self, title, body):
        # TODO: we might want to add category here, but there is no use on iOS side for now
        return Payload(
            alert={"title": title, "body": body}, sound="default", badge=0, mutable_content=True
        )

    def create_shadow_payload(self, body):
        return Payload(content_available=True, custom=body, mutable_content=True)

    def send_many_notifications(self, tokens, payload):
        notifications = [Notification(token, payload) for token in tokens]
        self.client.send_notification_batch(notifications=notifications, topic=self.topic)

    def send_one_notification(self, token, payload):
        self.client.send_notification(token, payload, self.topic)


IOSNotificationSender = IOSNotificationWrapper()
AndroidNotificationSender = AndroidNotificationWrapper()
IOSNotificationDevSender = IOSNotificationWrapper(is_dev=True)


@shared_task(name="notifications.ios_send_notification")
def ios_send_notification(tokens, title, body):
    IOSNotificationSender.send_notification(tokens, title, body)


@shared_task(name="notifications.ios_send_shadow_notification")
def ios_send_shadow_notification(tokens, body):
    IOSNotificationSender.send_shadow_notification(tokens, body)


@shared_task(name="notifications.android_send_notification")
def android_send_notification(tokens, title, body):
    AndroidNotificationSender.send_notification(tokens, title, body)


@shared_task(name="notifications.android_send_shadow_notification")
def android_send_shadow_notification(tokens, body):
    AndroidNotificationSender.send_shadow_notification(tokens, body)


@shared_task(name="notifications.ios_send_dev_notification")
def ios_send_dev_notification(tokens, title, body):
    IOSNotificationDevSender.send_notification(tokens, title, body)


@shared_task(name="notifications.ios_send_dev_shadow_notification")
def ios_send_dev_shadow_notification(tokens, body):
    IOSNotificationDevSender.send_shadow_notification(tokens, body)
