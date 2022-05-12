import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

import user.notifications as notif
from gsr_booking.models import GSR, Group, GSRBooking, Reservation
from user.models import NotificationSetting, NotificationToken


User = get_user_model()


def mock_send_notif(*args, **kwargs):
    # used for mocking notification sends
    return


def mock_get_path(*args, **kwargs):
    # used for mocking notification sends
    return ""


class TestNotificationToken(TestCase):
    """Tests for CRUD Notification Tokens"""

    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

    def test_post_save(self):
        # asserts that post save hook in creating tokens works correctly
        self.assertEqual(1, NotificationToken.objects.all().count())
        self.assertEqual(self.test_user, NotificationToken.objects.all().first().user)

    def test_create_update_token(self):
        # test that creating token returns correct response
        payload = {"kind": "IOS", "dev": "false", "token": "test123"}
        response = self.client.post("/user/notifications/tokens/", payload)
        res_json = json.loads(response.content)
        self.assertEqual("IOS", res_json["kind"])
        self.assertFalse(res_json["dev"])
        self.assertEqual("test123", res_json["token"])
        self.assertEqual(3, len(res_json))
        self.assertEqual(1, NotificationToken.objects.all().count())

        # new payload, should not create a new token
        new_payload = {"kind": "IOS", "dev": "false", "token": "newtoken"}
        response = self.client.post("/user/notifications/tokens/", new_payload)
        res_json = json.loads(response.content)
        self.assertEqual("newtoken", res_json["token"])
        self.assertEqual(1, NotificationToken.objects.all().count())

    def test_get_token(self):
        # test that tokens are visible via GET
        payload = {"kind": "IOS", "dev": "false", "token": "test123"}
        response = self.client.post("/user/notifications/tokens/", payload)

        response = self.client.get("/user/notifications/tokens/")
        res_json = json.loads(response.content)
        self.assertEqual("IOS", res_json[0]["kind"])
        self.assertFalse(res_json[0]["dev"])
        self.assertEqual("test123", res_json[0]["token"])
        self.assertEqual(1, len(res_json))
        self.assertEqual(3, len(res_json[0]))
        self.assertEqual(1, NotificationToken.objects.all().count())


class TestNotificationSetting(TestCase):
    """Tests for CRUD Notification Settings"""

    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

    def test_get_settings(self):
        # test that settings visible via GET
        response = self.client.get("/user/notifications/settings/")
        res_json = json.loads(response.content)
        self.assertEqual(len(NotificationSetting.SERVICE_OPTIONS), len(res_json))
        for setting in res_json:
            self.assertFalse(setting["enabled"])

    def test_create_update_check_settings(self):
        # test that invalid settings are rejected
        payload = {"service": "Penn Mobile", "enabled": True}
        response = self.client.post("/user/notifications/settings/", payload)
        res_json = json.loads(response.content)
        self.assertNotEqual(res_json, payload)

        # test that settings can be created and updated via POST
        payload = {"service": "PENN_MOBILE", "enabled": True}
        response = self.client.post("/user/notifications/settings/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(res_json, payload)

        # since token empty, should still return false
        response = self.client.get("/user/notifications/settings/PENN_MOBILE/check/")
        res_json = json.loads(response.content)
        self.assertFalse(res_json["enabled"])
        self.assertTrue(res_json["missing_token"])

        # update token to nonempty value
        payload = {"kind": "IOS", "dev": False, "token": "test123"}
        response = self.client.post("/user/notifications/tokens/", payload)
        res_json = json.loads(response.content)
        self.assertEqual("test123", res_json["token"])
        self.assertEqual(1, NotificationToken.objects.all().count())

        # re-request check
        response = self.client.get("/user/notifications/settings/PENN_MOBILE/check/")
        res_json = json.loads(response.content)
        self.assertTrue(res_json["enabled"])
        self.assertFalse(res_json["missing_token"])

    def test_check_fail(self):
        # since invalid setting, should return error
        response = self.client.get("/user/notifications/settings/PENN_MOBIL/check/")
        res_json = json.loads(response.content)
        self.assertTrue("error" in res_json)


class TestNotificationAlert(TestCase):
    """Tests for sending Notification Alerts"""

    def setUp(self):
        self.client = APIClient()

        # create user2
        self.test_user = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        self.client.force_authenticate(user=self.test_user)
        token = NotificationToken.objects.get(user=self.test_user)
        token.token = "test234"
        token.save()
        setting = NotificationSetting.objects.get(token=token, service="PENN_MOBILE")
        setting.enabled = True
        setting.save()

        # create user1
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)
        token = NotificationToken.objects.get(user=self.test_user)
        token.token = "test123"
        token.save()

    @mock.patch("user.views.send_push_notif", mock_send_notif)
    def test_single_notif(self):
        # test notif fail when setting is false
        payload = {"title": "Test", "body": ":D", "service": "PENN_MOBILE"}
        response = self.client.post("/user/notifications/alerts/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(0, len(res_json["success_users"]))
        self.assertEqual(1, len(res_json["failed_users"]))

        # update setting
        payload = {"service": "PENN_MOBILE", "enabled": True}
        response = self.client.post("/user/notifications/settings/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(res_json, payload)

        # test notif success when setting is true
        payload = {"title": "Test", "body": ":D", "service": "PENN_MOBILE"}
        response = self.client.post("/user/notifications/alerts/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json["success_users"]))
        self.assertEqual(0, len(res_json["failed_users"]))

    @mock.patch("user.views.send_push_notif_batch", mock_send_notif)
    def test_batch_notif(self):
        # update setting for first user
        payload = {"service": "PENN_MOBILE", "enabled": True}
        response = self.client.post("/user/notifications/settings/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(res_json, payload)

        # test notif
        payload = {
            "users": ["user", "user2", "user3"],
            "title": "Test",
            "body": ":D",
            "service": "PENN_MOBILE",
        }
        response = self.client.post(
            "/user/notifications/alerts/", json.dumps(payload), content_type="application/json"
        )
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json["success_users"]))
        self.assertEqual(1, len(res_json["failed_users"]))


class TestSendGSRReminders(TestCase):
    """Test Sending GSR Reminders"""

    def setUp(self):
        call_command("load_gsrs")
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

        # enabling tokens and settings
        token = NotificationToken.objects.get(user=self.test_user)
        token.token = "test123"
        token.save()

        setting = NotificationSetting.objects.get(
            token=token, service=NotificationSetting.SERVICE_GSR_BOOKING
        )
        setting.enabled = True
        setting.save()

        # creating reservation and booking for notifs
        g = GSRBooking.objects.create(
            user=self.test_user,
            gsr=GSR.objects.all().first(),
            room_id=1,
            room_name="Room",
            start=timezone.now() + datetime.timedelta(minutes=5),
            end=timezone.now() + datetime.timedelta(minutes=35),
        )

        r = Reservation.objects.create(
            start=g.start,
            end=g.end,
            creator=self.test_user,
            group=Group.objects.get(owner=self.test_user),
        )

        g.reservation = r
        g.save()

    @mock.patch(
        "gsr_booking.management.commands.send_gsr_reminders.send_push_notif", mock_send_notif
    )
    def test_send_reminder(self):
        # mock the notification send via mock_send_notif
        call_command("send_gsr_reminders")
        # test that reservation reminder was sent
        r = Reservation.objects.all().first()
        self.assertTrue(r.reminder_sent)


class TestSendShadowNotifs(TestCase):
    """Test Sending Shadow Notifications"""

    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)
        token = NotificationToken.objects.get(user=self.test_user)
        token.token = "test123"
        token.save()

    @mock.patch(
        "user.management.commands.send_shadow_notifs.send_shadow_push_notif_batch", mock_send_notif
    )
    def test_shadow_notifications(self):
        # mock the notification send via mock_send_notif

        # call command on every user
        call_command("send_shadow_notifs", "yes", '{"test":"test"}')

        # call command on specific set of users
        call_command("send_shadow_notifs", "no", '{"test":"test"}', usernames="user1")


class TestCallingNotificationsAPI(TestCase):
    """Test Calling API Notifications"""

    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)
        token = NotificationToken.objects.get(user=self.test_user)
        token.token = "test123"
        token.save()

    @mock.patch("os.path.join", mock_get_path)
    @mock.patch("apns2.client.APNsClient.send_notification", mock_send_notif)
    def test_send_push_notif(self):
        token = NotificationToken.objects.first()
        notif.send_push_notif(token=token, title="title", body="body")

    @mock.patch("os.path.join", mock_get_path)
    @mock.patch("apns2.client.APNsClient.send_notification_batch", mock_send_notif)
    def test_send_push_notif_batch(self):
        token = NotificationToken.objects.first()
        notif.send_push_notif_batch(tokens=[token], title="title", body="body")

    @mock.patch("os.path.join", mock_get_path)
    @mock.patch("apns2.client.APNsClient.send_notification_batch", mock_send_notif)
    def test_send_shadow_push_notif_batch(self):
        token = NotificationToken.objects.first()
        notif.send_shadow_push_notif_batch(tokens=[token], body=dict())
