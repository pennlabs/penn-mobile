import datetime
import json
from typing import Any
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from portal.models import Poll, PollOption, PollVote
from utils.types import DjangoUserModel, UserType


def mock_get_user_clubs(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    with open("tests/portal/get_user_clubs.json") as data:
        return json.load(data)


class PollPermissions(TestCase):
    def setUp(self) -> None:
        call_command("load_target_populations", "--years", "2022, 2023, 2024, 2025")

        self.client: APIClient = APIClient()
        self.admin: UserType = DjangoUserModel.objects.create_superuser(
            "admin@example.com", "admin", "admin"
        )
        self.user1: UserType = DjangoUserModel.objects.create_user(
            "user1", "user@seas.upenn.edu", "user"
        )
        self.user2: UserType = DjangoUserModel.objects.create_user(
            "user2", "user@seas.upenn.edu", "user"
        )

        self.poll_1: Poll = Poll.objects.create(
            club_code="pennlabs",
            question="poll question 1",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            status=Poll.STATUS_APPROVED,
        )

        self.poll_option_1: PollOption = PollOption.objects.create(
            poll=self.poll_1, choice="hello!"
        )
        self.poll_option_2: PollOption = PollOption.objects.create(
            poll=self.poll_1, choice="hello!!!!"
        )
        self.poll_option_3: PollOption = PollOption.objects.create(
            poll=self.poll_1, choice="hello!!!!!!!"
        )

        self.poll_2: Poll = Poll.objects.create(
            club_code="pennlabs",
            question="poll question 2",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            status=Poll.STATUS_APPROVED,
        )

        self.poll_vote: PollVote = PollVote.objects.create(id_hash="2", poll=self.poll_1)
        self.poll_vote.poll_options.add(self.poll_option_1)

    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    def test_authentication(self) -> None:
        # asserts that anonymous users cannot access any route
        list_urls = ["poll-list", "polloption-list", "pollvote-list", "target-populations"]
        for url in list_urls:
            response_1 = self.client.get(reverse(f"portal:{url}"))
            self.assertEqual(response_1.status_code, 403)

        arg_urls = ["poll-detail", "polloption-detail", "pollvote-detail"]
        for url in arg_urls:
            response_2 = self.client.get(reverse(f"portal:{url}", args=[self.poll_1.id]))
            self.assertEqual(response_2.status_code, 403)

    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.views.get_user_clubs", mock_get_user_clubs)
    def test_update_poll(self) -> None:
        # users in same club can edit
        self.client.force_authenticate(user=self.user2)
        payload_1 = {"status": Poll.STATUS_REVISION}
        response_1 = self.client.patch(
            reverse("portal:poll-detail", args=[self.poll_1.id]), payload_1
        )
        # 404 because queryset denies access
        self.assertEqual(response_1.status_code, 200)

        # admin can update polls
        self.client.force_authenticate(user=self.admin)
        payload_2 = {"status": Poll.STATUS_REVISION}
        response_2 = self.client.patch(
            reverse("portal:poll-detail", args=[self.poll_1.id]), payload_2
        )
        self.assertEqual(response_2.status_code, 200)

    @mock.patch("portal.permissions.get_user_clubs", mock_get_user_clubs)
    @mock.patch("portal.views.get_user_clubs", mock_get_user_clubs)
    def test_create_update_options(self) -> None:
        # users in same club can edit poll option
        self.client.force_authenticate(user=self.user2)
        payload_1 = {"poll": self.poll_1.id, "choice": "hello"}
        response_1 = self.client.post("/portal/options/", payload_1)
        res_json_1 = json.loads(response_1.content)
        self.assertEqual(response_1.status_code, 201)

        payload_2 = {"choice": "helloooo"}
        response_2 = self.client.patch(
            reverse("portal:polloption-detail", args=[res_json_1["id"]]), payload_2
        )
        self.assertEqual(response_2.status_code, 200)

        # admin can create poll option
        self.client.force_authenticate(user=self.admin)
        payload_3 = {"choice": "helloooo"}
        response_3 = self.client.patch(
            reverse("portal:polloption-detail", args=[res_json_1["id"]]), payload_3
        )
        self.assertEqual(response_3.status_code, 200)
