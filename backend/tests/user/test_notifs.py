import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from identity.identity import attest, container, get_platform_jwks
from rest_framework.test import APIClient

from user.models import IOSNotificationToken, NotificationService


User = get_user_model()


def initialize_b2b():
    get_platform_jwks()
    attest()


def get_b2b_client():
    client = APIClient()
    client.logout()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + container.access_jwt.serialize())
    return client


class MockAPNsClient:
    def send_notification(self, token, payload, topic):
        del token, payload, topic
        pass

    def send_notification_batch(self, notifications, topic):
        del notifications, topic
        pass


def mock_client(is_dev):
    return MockAPNsClient()


class TestIOSNotificationToken(TestCase):
    """Tests for associating and deleting IOS Notification Tokens"""

    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)
        self.token = "1234"

    def test_create_token(self):
        response = self.client.post(f"/user/notifications/tokens/ios/{self.token}/")
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, IOSNotificationToken.objects.all().count())
        the_token = IOSNotificationToken.objects.first()
        self.assertEqual(self.token, the_token.token)
        self.assertEqual(self.test_user, the_token.user)
        self.assertEqual(False, the_token.is_dev)

    def test_update_token(self):
        # test that posting to same token updates the token
        user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        IOSNotificationToken.objects.create(user=user2, token=self.token, is_dev=True)

        response = self.client.post(f"/user/notifications/tokens/ios/{self.token}/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, IOSNotificationToken.objects.all().count())
        the_token = IOSNotificationToken.objects.first()
        self.assertEqual(self.token, the_token.token)
        self.assertEqual(self.test_user, the_token.user)
        self.assertEqual(False, the_token.is_dev)

    def test_delete_token(self):
        response = self.client.post(f"/user/notifications/tokens/ios/{self.token}/")
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, IOSNotificationToken.objects.all().count())

        response = self.client.delete(f"/user/notifications/tokens/ios/{self.token}/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, IOSNotificationToken.objects.all().count())


class TestNotificationService(TransactionTestCase):
    """Tests for CRUD Notification Settings"""

    def setUp(self):
        NotificationService.objects.bulk_create(
            [
                NotificationService(name="PENN_MOBILE"),
                NotificationService(name="OHQ"),
            ]
        )
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

    def test_get_services(self):
        # test that services visible via GET
        response = self.client.get("/user/notifications/services/")
        res_json = json.loads(response.content)
        self.assertEqual(["OHQ", "PENN_MOBILE"], sorted(res_json))

    def test_get_settings(self):
        response = self.client.get("/user/notifications/settings/")
        res_json = json.loads(response.content)
        self.assertDictEqual({"PENN_MOBILE": False, "OHQ": False}, res_json)

    def test_update_settings(self):
        response = self.client.put(
            "/user/notifications/settings/",
            json.dumps({"PENN_MOBILE": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)

        response = self.client.get("/user/notifications/settings/")
        res_json = json.loads(response.content)
        self.assertDictEqual({"PENN_MOBILE": True, "OHQ": False}, res_json)

    def test_invalid_settings_update(self):
        # Requires TransactionTestCase since relies on database rollback
        response = self.client.put(
            "/user/notifications/settings/",
            json.dumps({"UNKNOWN": True, "sPENN_MOBILE": True, "ABC": True, "OHQ": True}),
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)


class TestNotificationAlert(TestCase):
    """Tests for sending Notification Alerts"""

    def setUp(self):
        self.client = APIClient()

        NotificationService.objects.bulk_create(
            [
                NotificationService(name="PENN_MOBILE"),
                NotificationService(name="OHQ"),
            ]
        )

        user1 = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        IOSNotificationToken.objects.create(user=user1, token="test123")

        user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        IOSNotificationToken.objects.create(user=user2, token="test234")
        user2.notificationservice_set.add("PENN_MOBILE")

        # create user3
        user3 = User.objects.create_user("user3", "user3@seas.upenn.edu", "user3")
        IOSNotificationToken.objects.create(user=user3, token="test345")
        user3.notificationservice_set.add("PENN_MOBILE")

        self.client.force_authenticate(user=user3)

        initialize_b2b()

    @mock.patch("user.notifications.get_client", mock_client)
    def test_failed_notif(self):
        # missing title
        payload = {"body": ":D", "service": "PENN_MOBILE"}
        response = self.client.post("/user/notifications/alerts/", payload)
        self.assertEqual(response.status_code, 400)

        payload["title"] = "Test"
        response = self.client.post("/user/notifications/alerts/", payload)
        self.assertEqual(response.status_code, 200)

        # invalid service
        payload = {"body": ":D", "service": "OHS"}
        response = self.client.post("/user/notifications/alerts/", payload)
        self.assertEqual(response.status_code, 400)

    @mock.patch("user.notifications.get_client", mock_client)
    def test_single_notif(self):
        # test notif fail when setting is false
        payload = {"title": "Test", "body": ":D", "service": "OHQ"}
        response = self.client.post("/user/notifications/alerts/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(0, len(res_json["success_users"]))
        self.assertEqual(1, len(res_json["failed_users"]))

        # test notif success when setting is true
        payload = {"title": "Test", "body": ":D", "service": "PENN_MOBILE"}
        response = self.client.post("/user/notifications/alerts/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json["success_users"]))
        self.assertEqual(0, len(res_json["failed_users"]))


# TODO: FIX IN LATER PR

# class TestSendGSRReminders(TestCase):
#     """Test Sending GSR Reminders"""

#     def setUp(self):
#         call_command("load_gsrs")
#         self.client = APIClient()
#         user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
#         user.iosnotificationtoken_set.create(token="test123")


#         setting = NotificationSetting.objects.get(
#             token=token_obj, service=NotificationSetting.SERVICE_GSR_BOOKING
#         )
#         setting.enabled = True
#         setting.save()

#         # creating reservation and booking for notifs
#         g = GSRBooking.objects.create(
#             user=self.test_user,
#             gsr=GSR.objects.all().first(),
#             room_id=1,
#             room_name="Room",
#             start=timezone.now() + datetime.timedelta(minutes=5),
#             end=timezone.now() + datetime.timedelta(minutes=35),
#         )

#         r = Reservation.objects.create(
#             start=g.start,
#             end=g.end,
#             creator=self.test_user,
#         )

#         g.reservation = r
#         g.save()

#     @mock.patch("user.notifications.get_client", mock_client)
#     def test_send_reminder(self):
#         call_command("send_gsr_reminders")
#         r = Reservation.objects.all().first()
#         self.assertTrue(r.reminder_sent)

#     def test_send_reminder_no_gsrs(self):
#         GSRBooking.objects.all().delete()
#         call_command("send_gsr_reminders")
#         r = Reservation.objects.all().first()
#         self.assertFalse(r.reminder_sent)


# class TestSendShadowNotifs(TestCase):
#     """Test Sending Shadow Notifications"""

#     def setUp(self):
#         self.client = APIClient()
#         self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
#         self.client.force_authenticate(user=self.test_user)
#         token_obj = IOSNotificationToken.objects.get(user=self.test_user)
#         token_obj.token = "test123"
#         token_obj.save()

#     @mock.patch("user.notifications.get_client", mock_client)
#     def test_shadow_notifications(self):
#         # call command on every user
#         call_command("send_shadow_notifs", "yes", '{"test":"test"}')

#         # call command on specific set of users
#         call_command("send_shadow_notifs", "no", '{"test":"test"}', users="user1")
