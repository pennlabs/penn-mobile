from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from utils.email import get_backend_manager_emails, send_automated_email, send_mail


User = get_user_model()


class EmailTestCase(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="backend_managers")
        self.user1 = User.objects.create_user(
            username="user1", password="password", email="user1@domain.com"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password", email="user2@domain.com"
        )
        self.user3 = User.objects.create_user(username="user3", password="password")

        self.group.user_set.add(self.user1)
        self.group.user_set.add(self.user3)

    @mock.patch("utils.email.django_send_mail")
    def test_send_mail(self, mock_send_mail):
        send_mail("testing321", ["test@example.com"], message="test message?!")
        mock_send_mail.assert_called_once_with(
            subject="testing321",
            message="test message?!",
            from_email=None,
            recipient_list=["test@example.com"],
            fail_silently=False,
            html_message=None,
        )

    def test_send_mail_error(self):
        with self.assertRaises(ValueError):
            send_mail("testing321", None, message="test message?!")

    @mock.patch("utils.email.django_send_mail")
    def test_send_automated_email(self, mock_send_mail):
        send_automated_email("testing123", ["test@example.com"], "test message?!")
        html_message = mock_send_mail.call_args[1]["html_message"]
        mock_send_mail.assert_called_once_with(
            subject="testing123",
            message=None,
            from_email=None,
            recipient_list=["test@example.com"],
            fail_silently=False,
            html_message=html_message,
        )
        self.assertIsNotNone(html_message)
        self.assertIn("test message?!", html_message)

    def test_get_backend_manager_emails(self):
        emails = get_backend_manager_emails()
        self.assertEqual(emails, ["user1@domain.com"])

        self.group.delete()
        emails = get_backend_manager_emails()
        self.assertEqual(emails, [])
