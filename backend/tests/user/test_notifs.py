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


class TestNotificationAlert(TestCase):
    """Tests for sending Notification Alerts"""

    def setUp(self):
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)


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
