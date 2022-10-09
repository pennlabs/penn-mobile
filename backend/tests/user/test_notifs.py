import datetime
import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

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
        NotificationToken.objects.all().delete()

        # test that creating token returns correct response
        payload = {"kind": "IOS", "dev": "false", "token": "test123"}
        response = self.client.post("/user/notifications/tokens/", payload)
        res_json = json.loads(response.content)
        self.assertEqual("IOS", res_json["kind"])
        self.assertFalse(res_json["dev"])
        self.assertEqual("test123", res_json["token"])
        self.assertEqual(4, len(res_json))
        self.assertEqual(1, NotificationToken.objects.all().count())

        # update token
        new_payload = {"kind": "IOS", "token": "newtoken"}
        response = self.client.patch(f"/user/notifications/tokens/{res_json['id']}/", new_payload)
        res_json = json.loads(response.content)
        self.assertEqual("newtoken", res_json["token"])
        self.assertEqual(1, NotificationToken.objects.all().count())

    def test_get_token(self):
        NotificationToken.objects.all().delete()

        # create token
        payload = {"kind": "IOS", "dev": "false", "token": "test123"}
        response = self.client.post("/user/notifications/tokens/", payload)

        response = self.client.get("/user/notifications/tokens/")
        res_json = json.loads(response.content)
        self.assertEqual("IOS", res_json[0]["kind"])
        self.assertFalse(res_json[0]["dev"])
        self.assertEqual("test123", res_json[0]["token"])
        self.assertEqual(1, len(res_json))
        self.assertEqual(4, len(res_json[0]))
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
        NotificationSetting.objects.filter(service="PENN_MOBILE").delete()
        payload = {"service": "Penn Mobile", "enabled": True}
        response = self.client.post("/user/notifications/settings/", payload)
        res_json = json.loads(response.content)
        self.assertNotEqual(res_json, payload)

        # test that settings can be created
        payload = {"service": "PENN_MOBILE", "enabled": True}
        response = self.client.post("/user/notifications/settings/", payload)
        res_json = json.loads(response.content)
        self.assertEqual(res_json["service"], "PENN_MOBILE")
        self.assertTrue(res_json["enabled"])

        # since token empty, should still return false
        response = self.client.get("/user/notifications/settings/PENN_MOBILE/check/")
        res_json = json.loads(response.content)
        self.assertFalse(res_json["enabled"])

        # since token empty, should still return false
        response = self.client.get("/user/notifications/tokens/")
        res_json = json.loads(response.content)
        token_id = res_json[0]["id"]

        # update token to nonempty value
        payload = {"kind": "IOS", "dev": False, "token": "test123"}
        response = self.client.put(f"/user/notifications/tokens/{token_id}/", payload)
        res_json = json.loads(response.content)
        self.assertEqual("test123", res_json["token"])
        self.assertEqual(1, NotificationToken.objects.all().count())

        # re-request check
        response = self.client.get("/user/notifications/settings/PENN_MOBILE/check/")
        res_json = json.loads(response.content)
        self.assertTrue(res_json["enabled"])

    def test_check_fail(self):
        # since invalid setting, should return error
        response = self.client.get("/user/notifications/settings/PENN_MOBIL/check/")
        self.assertEqual(response.status_code, 400)


class TestNotificationAlert(TestCase):
    """Tests for sending Notification Alerts"""

    def setUp(self):
        self.client = APIClient()

        # create user1
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)
        token_obj = NotificationToken.objects.get(user=self.test_user)
        token_obj.token = "test123"
        token_obj.save()

        # create user2
        self.test_user = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
        self.client.force_authenticate(user=self.test_user)
        token_obj = NotificationToken.objects.get(user=self.test_user)
        token_obj.token = "test234"
        token_obj.save()
        setting = NotificationSetting.objects.get(token=token_obj, service="PENN_MOBILE")
        setting.enabled = True
        setting.save()

    @mock.patch("user.notifications.send_immediate_notifications", mock_send_notif)
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

    @mock.patch("user.notifications.send_immediate_notifications", mock_send_notif)
    def test_batch_notif(self):
        # update all settings to be enabled
        NotificationSetting.objects.all().update(enabled=True)

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
        token_obj = NotificationToken.objects.get(user=self.test_user)
        token_obj.token = "test123"
        token_obj.save()

        setting = NotificationSetting.objects.get(
            token=token_obj, service=NotificationSetting.SERVICE_GSR_BOOKING
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

    @mock.patch("user.notifications.send_immediate_notifications", mock_send_notif)
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
        token_obj = NotificationToken.objects.get(user=self.test_user)
        token_obj.token = "test123"
        token_obj.save()

    @mock.patch("user.notifications.send_immediate_notifications", mock_send_notif)
    def test_shadow_notifications(self):
        # mock the notification send via mock_send_notif

        # call command on every user
        call_command("send_shadow_notifs", "yes", '{"test":"test"}')

        # call command on specific set of users
        call_command("send_shadow_notifs", "no", '{"test":"test"}', usernames="user1")
