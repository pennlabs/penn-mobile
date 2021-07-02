import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from user.models import NotificationSetting, NotificationToken


User = get_user_model()


class NotificationSettingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user", "user@a.com", "password")
        self.client = APIClient()
        self.client.login(username="user", password="password")

        NotificationSetting.objects.create(user=self.user, setting="gsr", enabled=False)
        NotificationSetting.objects.create(user=self.user, setting="dining", enabled=False)
        NotificationSetting.objects.create(user=self.user, setting="laundry", enabled=True)

    def test_get_notif_settings(self):

        response = self.client.get(reverse("notif-settings"))
        res_json = json.loads(response.content)

        # test if settings were enabled / not enabled
        self.assertEqual(200, response.status_code)
        self.assertFalse(res_json["settings"]["gsr"])
        self.assertFalse(res_json["settings"]["dining"])
        self.assertTrue(res_json["settings"]["laundry"])

    def test_post_notif_settings(self):

        data = {"gsr": True, "dining": True, "asdf": False}
        response = self.client.post(reverse("notif-settings"), data)
        res_json = json.loads(response.content)
        self.assertEqual("success", res_json["detail"])

        # assert that settings only change if there is a new setting
        response = self.client.get(reverse("notif-settings"))
        res_json = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(res_json["settings"]["gsr"])
        self.assertTrue(res_json["settings"]["dining"])
        self.assertTrue(res_json["settings"]["laundry"])
        self.assertFalse(res_json["settings"]["asdf"])
        self.assertEqual(4, NotificationSetting.objects.all().count())


class NotificationTokenTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("user", "user@a.com", "password")
        self.client = APIClient()
        self.client.login(username="user", password="password")

    def test_post_notif_register_1(self):

        # test that all tokens are in order
        self.assertEqual(0, NotificationToken.objects.all().count())
        data = {
            "dev": True,
            "ios_token": "12345",
        }
        response = self.client.post(reverse("notif-register"), data)
        res_json = json.loads(response.content)
        self.assertEqual("success", res_json["detail"])
        self.assertEqual(1, NotificationToken.objects.all().count())
        token_obj = NotificationToken.objects.all().first()
        self.assertEqual(self.user, token_obj.user)
        self.assertEqual("12345", token_obj.token)
        self.assertTrue(token_obj.dev)

    def test_post_notif_register_2(self):
        self.assertEqual(0, NotificationToken.objects.all().count())
        data = {
            "dev": True,
            "ios_token": "12345",
        }
        self.client.post(reverse("notif-register"), data)
        self.assertEqual(1, NotificationToken.objects.all().count())
        token_obj = NotificationToken.objects.all().first()
        self.assertEqual("12345", token_obj.token)
        # changes iOS token
        data["ios_token"] = "54321"
        self.client.post(reverse("notif-register"), data)
        # assert that no new object has been made, previous object was edited
        self.assertEqual(1, NotificationToken.objects.all().count())
        token_obj = NotificationToken.objects.all().first()
        self.assertEqual("54321", token_obj.token)
