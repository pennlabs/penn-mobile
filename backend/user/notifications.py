import collections
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
    def send_notification(self, tokens, title, body, urgent):
        self.send_payload(tokens, self.create_payload(title, body, urgent))

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
    def create_payload(self, title, body, urgent):
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
            auth_key_path = "/app/secrets/notifications/android/fcm.json"
            cred = credentials.Certificate(auth_key_path)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Notifications Error: Failed to initialize Firebase client: {e}")

    def create_payload(self, title, body, urgent):
        # TODO: do something with urgent
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
    class CustomPayload(Payload):
        # Custom payload to support interruption_level
        def __init__(self, urgent, **kwargs):
            super().__init__(**kwargs)
            self.urgent = urgent

        def dict(self):
            result = super().dict()
            if self.urgent:
                result["aps"]["interruption-level"] = "time-sensitive"
            return result

    @staticmethod
    def get_client(is_dev):
        # TODO: We are getting a new client for each request, might be worth
        # looking into how to keep the client alive.
        auth_key_path = (
            f"/app/secrets/notifications/ios{'/dev/apns-dev' if is_dev else '/prod/apns-prod'}.pem"
        )
        return APNsClient(credentials=auth_key_path, use_sandbox=is_dev)

    def __init__(self, is_dev=False):
        try:
            self.is_dev = is_dev
            self.topic = "org.pennlabs.PennMobile" + (".dev" if is_dev else "")
        except Exception as e:
            print(f"Notifications Error: Failed to initialize APNs client: {e}")

    def create_payload(self, title, body, urgent):
        # TODO: we might want to add category here, but there is no use on iOS side for now
        return IOSNotificationWrapper.CustomPayload(
            alert={"title": title, "body": body},
            sound="default",
            badge=0,
            mutable_content=True,
            urgent=urgent,
        )

    def create_shadow_payload(self, body):
        return Payload(content_available=True, custom=body, mutable_content=True)

    def send_many_notifications(self, tokens, payload):
        notifications = [Notification(token, payload) for token in tokens]
        self.get_client(self.is_dev).send_notification_batch(
            notifications=notifications, topic=self.topic
        )

    def send_one_notification(self, token, payload):
        self.get_client(self.is_dev).send_notification(token, payload, self.topic)


IOSNotificationSender = IOSNotificationWrapper()
AndroidNotificationSender = AndroidNotificationWrapper()
IOSNotificationDevSender = IOSNotificationWrapper(is_dev=True)


@shared_task(name="notifications.ios_send_notification")
def ios_send_notification(tokens, title, body, urgent):
    IOSNotificationSender.send_notification(tokens, title, body)


@shared_task(name="notifications.ios_send_shadow_notification")
def ios_send_shadow_notification(tokens, body):
    IOSNotificationSender.send_shadow_notification(tokens, body)


@shared_task(name="notifications.android_send_notification")
def android_send_notification(tokens, title, body, urgent):
    AndroidNotificationSender.send_notification(tokens, title, body)


@shared_task(name="notifications.android_send_shadow_notification")
def android_send_shadow_notification(tokens, body):
    AndroidNotificationSender.send_shadow_notification(tokens, body)


@shared_task(name="notifications.ios_send_dev_notification")
def ios_send_dev_notification(tokens, title, body, urgent):
    IOSNotificationDevSender.send_notification(tokens, title, body)


@shared_task(name="notifications.ios_send_dev_shadow_notification")
def ios_send_dev_shadow_notification(tokens, body):
    IOSNotificationDevSender.send_shadow_notification(tokens, body)
