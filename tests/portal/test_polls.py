import datetime
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from portal.models import Poll  # , PollOption, PollVote


User = get_user_model()


class TestPolls(TestCase):
    """Tests Create/Update/Retrieve for Polls and Poll Options"""

    def setUp(self):
        print("HELLO WENT HERE")
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@a.com", "user")
        self.client.force_authenticate(user=self.test_user)
        # creates an approved poll to work with
        payload = {
            "source": "Test Source 1",
            "question": "How is this question? 1",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 1",
        }
        self.client.post(reverse("create-poll"), payload)
        poll_1 = Poll.objects.all().first()
        poll_1.approved = True
        poll_1.save()
        self.id = poll_1.id

    def test_create_poll(self):
        # creates an unapproved poll
        payload = {
            "source": "Test Source 2",
            "question": "How is this question? 2",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 2",
        }
        response = self.client.post(reverse("create-poll"), payload)
        res_json = json.loads(response.content)
        # asserts that poll was created and that the admin comment cannot be made
        self.assertEqual(2, Poll.objects.all().count())
        self.assertEqual("Test Source 2", res_json["source"])
        self.assertEqual("", Poll.objects.get(id=res_json["id"]).admin_comment)

    def test_update_poll(self):
        payload = {
            "source": "New Test Source 3",
        }
        response = self.client.patch(reverse("update-poll", args=[self.id]), payload)
        res_json = json.loads(response.content)
        print(res_json)
        # asserts that the update worked
        self.assertEqual(1, res_json["id"])
        self.assertEqual("New Test Source 3", Poll.objects.get(id=1).source)

    def test_browse(self):
        payload = {
            "source": "Test Source 2",
            "question": "How is this question? 2",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 2",
        }
        self.client.post(reverse("create-poll"), payload)
        # asserts that you can only see approved polls
        response = self.client.get("/portal/polls/view/browse/")
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual(2, Poll.objects.all().count())

    #     def test_create_option(self):
    #         payload_1 = {"poll": 1, "choice": "yes!"}
    #         payload_2 = {"poll": 1, "choice": "no!"}
    #         self.client.post(reverse("create-option"), payload_1)
    #         self.client.post(reverse("create-option"), payload_2)
    #         self.assertEqual(2, PollOption.objects.all().count())
    #         # asserts options were created and were placed to right poll
    #         for poll_option in PollOption.objects.all():
    #             self.assertEqual(Poll.objects.get(id=1), poll_option.poll)
    #         response = self.client.get("/portal/polls/view/browse/")
    #         res_json = json.loads(response.content)
    #         self.assertEqual(2, len(res_json[0]["options"]))

    #     def test_update_option(self):
    #         payload_1 = {"poll": 1, "choice": "yes!"}
    #         response = self.client.post(reverse("create-option"), payload_1)
    #         res_json = json.loads(response.content)
    #         self.assertEqual("yes!", PollOption.objects.get(id=res_json["id"]).choice)
    #         payload_2 = {"poll": 1, "choice": "no!"}
    #         # checks that poll's option was changed
    #         self.client.patch(reverse("update-option", args=["1"]), payload_2)
    #         self.assertEqual("no!", PollOption.objects.get(id=res_json["id"]).choice)

    def test_review_poll(self):
        Poll.objects.create(
            user=self.test_user,
            source="hi",
            question="hello?",
            expire_date=timezone.now() + datetime.timedelta(days=3),
        )
        admin = User.objects.create_superuser("admin@example.com", "admin", "admin")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/portal/polls/view/review/")
        res_json = json.loads(response.content)
        # checks that admin can see unapproved polls
        self.assertEqual(1, len(res_json))
        self.assertEqual(2, Poll.objects.all().count())


# class TestPollVotes(TestCase):
#     '''Tests Create/Update Polls and History'''
#     def setUp(self):
#         self.client = APIClient()
#         self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
#         self.client.force_authenticate(user=self.test_user)

#         # creates 3 polls, each with 3 options
#         self.poll_user = User.objects.create_user("poll_user", "poll_user@a.com", "poll_user")
#         p1 = Poll.objects.create(
#             user=self.poll_user,
#             source="poll 1",
#             question="poll question 1",
#             expire_date=timezone.now() + datetime.timedelta(days=1),
#             approved=True,
#         )
#         PollOption.objects.create(poll=p1, choice="choice 1")
#         PollOption.objects.create(poll=p1, choice="choice 2")
#         PollOption.objects.create(poll=p1, choice="choice 3")
#         p2 = Poll.objects.create(
#             user=self.poll_user,
#             source="poll 2",
#             question="poll question 2",
#             expire_date=timezone.now() + datetime.timedelta(days=2),
#             approved=True,
#         )
#         PollOption.objects.create(poll=p2, choice="choice 4")
#         PollOption.objects.create(poll=p2, choice="choice 5")
#         PollOption.objects.create(poll=p2, choice="choice 6")
#         p3 = Poll.objects.create(
#             user=self.poll_user,
#             source="poll 3",
#             question="poll question 3",
#             expire_date=timezone.now() - datetime.timedelta(days=3),
#             approved=True,
#         )
#         PollOption.objects.create(poll=p3, choice="choice 7")
#         PollOption.objects.create(poll=p3, choice="choice 8")
#         PollOption.objects.create(poll=p3, choice="choice 9")

#     def test_create_vote(self):
#         payload_1 = {"poll_option": 1}
#         response = self.client.post(reverse("create-vote"), payload_1)
#         res_json = json.loads(response.content)
#         # tests that voting works
#         self.assertEqual(1, res_json["poll_option"])
#         self.assertEqual(1, PollVote.objects.all().count())
#         self.assertEqual(self.test_user, PollVote.objects.all().first().user)

#     def test_update_vote(self):
#         payload_1 = {"poll_option": 1}
#         self.client.post(reverse("create-vote"), payload_1)
#         payload_2 = {"poll_option": 3}
#         response = self.client.patch(reverse("update-vote", args=["1"]), payload_2)
#         res_json = json.loads(response.content)
#         # test that updating vote works
#         self.assertEqual(3, res_json["poll_option"])
#         self.assertEqual(1, PollVote.objects.all().count())
#         self.assertEqual(self.test_user, PollVote.objects.all().first().user)
#         self.assertEqual(3, PollVote.objects.all().first().poll_option.id)
#         self.assertEqual(1, PollVote.objects.all().first().poll.id)

#     def test_history(self):
#         payload_1 = {"poll_option": 1}
#         self.client.post(reverse("create-vote"), payload_1)
#         response = self.client.get(reverse("poll-history"))
#         res_json = json.loads(response.content)
#         # asserts that history works, can see expired posts and posts that
#         # user voted for
#         # also asserts that data collection works
#         self.assertEqual(3, len(res_json[0]["poll"]["options"]))
#         self.assertEqual(1, res_json[0]["poll_statistics"][0]["choice 1"]["schools"]["SEAS"])
#         self.assertEqual(3, len(res_json[1]["poll"]["options"]))
#         self.assertEqual({}, res_json[1]["poll_statistics"][0]["choice 7"]["schools"])
