import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from portal.models import Poll, PollOption, PollVote


User = get_user_model()


class PollPermissions(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser("admin@example.com", "admin", "admin")
        self.user1 = User.objects.create_user("user1", "user@seas.upenn.edu", "user")
        self.user2 = User.objects.create_user("user2", "user@seas.upenn.edu", "user")

        self.poll_1 = Poll.objects.create(
            user=self.user1,
            source="poll 1",
            question="poll question 1",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
        )

        self.poll_option_1 = PollOption.objects.create(poll=self.poll_1, choice="hello!")
        self.poll_option_2 = PollOption.objects.create(poll=self.poll_1, choice="hello!!!!")
        self.poll_option_3 = PollOption.objects.create(poll=self.poll_1, choice="hello!!!!!!!")

        self.poll_2 = Poll.objects.create(
            user=self.user2,
            source="poll 2",
            question="poll question 2",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
        )

        self.poll_vote = PollVote.objects.create(user=self.user2, poll=self.poll_1)
        self.poll_vote.poll_options.add(self.poll_option_1)

    def test_authentication(self):
        # asserts that anonymous users cannot access any route
        list_urls = [
            "poll-list",
            "polloption-list",
            "pollvote-list",
            "poll-history",
            "target-populations",
        ]
        for url in list_urls:
            response_1 = self.client.get(reverse(f"portal:{url}"))
            self.assertEqual(response_1.status_code, 403)

        arg_urls = ["poll-detail", "polloption-detail", "pollvote-detail", "vote-statistics"]
        for url in arg_urls:
            response_2 = self.client.get(reverse(f"portal:{url}", args=[self.poll_1.id]))
            self.assertEqual(response_2.status_code, 403)

    def test_update_poll(self):
        # users who didn't create poll cannot update
        self.client.force_authenticate(user=self.user2)
        payload_1 = {"approved": False}
        response_1 = self.client.patch(
            reverse("portal:poll-detail", args=[self.poll_1.id]), payload_1
        )
        # 404 because queryset denies access
        self.assertEqual(response_1.status_code, 404)

        # admin can update polls
        self.client.force_authenticate(user=self.admin)
        payload_2 = {"approved": False}
        response_2 = self.client.patch(
            reverse("portal:poll-detail", args=[self.poll_1.id]), payload_2
        )
        self.assertEqual(response_2.status_code, 200)

    def test_create_update_options(self):
        # users who didn't create poll cannot create/update corresponding poll option
        self.client.force_authenticate(user=self.user2)
        payload_1 = {"poll": self.poll_1.id, "choice": "hello"}
        response_1 = self.client.post("/portal/options/", payload_1)
        self.assertEqual(response_1.status_code, 403)

        payload_2 = {"choice": "helloooo"}
        response_2 = self.client.patch(
            reverse("portal:polloption-detail", args=[self.poll_1.id]), payload_2
        )
        # 404 because queryset denies access
        self.assertEqual(response_2.status_code, 404)

        # admin can create poll option
        self.client.force_authenticate(user=self.admin)
        payload_3 = {"choice": "helloooo"}
        response_3 = self.client.patch(
            reverse("portal:poll-detail", args=[self.poll_1.id]), payload_3
        )
        self.assertEqual(response_3.status_code, 200)

    def test_update_votes(self):
        # user cannot update other user votes
        self.client.force_authenticate(user=self.user1)
        payload_1 = {"poll_options": [self.poll_option_1.id]}
        response_1 = self.client.patch(
            reverse("portal:pollvote-detail", args=[self.poll_vote.id]), payload_1
        )
        # 404 because queryset denies access
        self.assertEqual(response_1.status_code, 404)

        # user can update own vote
        self.client.force_authenticate(user=self.user2)
        payload_2 = {"poll_options": [self.poll_option_2.id]}
        response_2 = self.client.patch(
            reverse("portal:pollvote-detail", args=[self.poll_vote.id]), payload_2
        )
        self.assertEqual(response_2.status_code, 200)

        # not even admin can update user vote
        self.client.force_authenticate(user=self.admin)
        payload_3 = {"poll_options": [self.poll_option_3.id]}
        response_3 = self.client.patch(
            reverse("portal:pollvote-detail", args=[self.poll_vote.id]), payload_3
        )
        # 404 because queryset denies access
        self.assertEqual(response_3.status_code, 404)
