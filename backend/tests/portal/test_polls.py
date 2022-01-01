import datetime
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from portal.models import Poll, PollOption, PollVote, TargetPopulation


User = get_user_model()


class TestPolls(TestCase):
    """Tests Create/Update/Retrieve for Polls and Poll Options"""

    def setUp(self):
        self.target_id = TargetPopulation.objects.create(population="SEAS").id
        self.client = APIClient()
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)
        # creates an approved poll to work with
        payload = {
            "source": "Test Source 1",
            "question": "How is this question? 1",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 1",
            "target_populations": [self.target_id],
        }
        self.client.post("/portal/polls/", payload)
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
            "target_populations": [self.target_id],
        }
        response = self.client.post("/portal/polls/", payload)
        res_json = json.loads(response.content)
        # asserts that poll was created and that the admin comment cannot be made
        self.assertEqual(2, Poll.objects.all().count())
        self.assertEqual("Test Source 2", res_json["source"])
        self.assertEqual(None, Poll.objects.get(id=res_json["id"]).admin_comment)

    def test_update_poll(self):
        payload = {
            "source": "New Test Source 3",
        }
        response = self.client.patch(f"/portal/polls/{self.id}/", payload)
        res_json = json.loads(response.content)
        # asserts that the update worked
        self.assertEqual(self.id, res_json["id"])
        self.assertEqual("New Test Source 3", Poll.objects.get(id=self.id).source)

    def test_browse(self):
        payload = {
            "source": "Test Source 2",
            "question": "How is this question? 2",
            "expire_date": timezone.localtime() + datetime.timedelta(days=1),
            "admin_comment": "asdfs 2",
            "target_populations": [self.target_id],
        }
        self.client.post("/portal/polls/", payload)
        # asserts that you can only see approved polls
        response = self.client.get("/portal/polls/browse/")
        res_json = json.loads(response.content)
        self.assertEqual(1, len(res_json))
        self.assertEqual(2, Poll.objects.all().count())

    def test_create_option(self):
        payload_1 = {"poll": self.id, "choice": "yes!"}
        payload_2 = {"poll": self.id, "choice": "no!"}
        self.client.post("/portal/options/", payload_1)
        self.client.post("/portal/options/", payload_2)
        self.assertEqual(2, PollOption.objects.all().count())
        # asserts options were created and were placed to right poll
        for poll_option in PollOption.objects.all():
            self.assertEqual(Poll.objects.get(id=self.id), poll_option.poll)
        response = self.client.get("/portal/polls/browse/")
        res_json = json.loads(response.content)
        self.assertEqual(2, len(res_json[0]["options"]))

    def test_update_option(self):
        payload_1 = {"poll": self.id, "choice": "yes!"}
        response = self.client.post("/portal/options/", payload_1)
        res_json = json.loads(response.content)
        self.assertEqual("yes!", PollOption.objects.get(id=res_json["id"]).choice)
        payload_2 = {"poll": self.id, "choice": "no!"}
        # checks that poll's option was changed
        self.client.patch(f'/portal/options/{res_json["id"]}/', payload_2)
        self.assertEqual("no!", PollOption.objects.get(id=res_json["id"]).choice)

    def test_review_poll(self):
        Poll.objects.create(
            user=self.test_user,
            source="hi",
            question="hello?",
            expire_date=timezone.now() + datetime.timedelta(days=3),
        )
        admin = User.objects.create_superuser("admin@example.com", "admin", "admin")
        self.client.force_authenticate(user=admin)
        response = self.client.get("/portal/polls/review/")
        res_json = json.loads(response.content)
        # checks that admin can see unapproved polls
        self.assertEqual(1, len(res_json))
        self.assertEqual(2, Poll.objects.all().count())

    def test_more_than_five_options(self):
        payload_1 = {"poll": self.id, "choice": "1"}
        payload_2 = {"poll": self.id, "choice": "2"}
        payload_3 = {"poll": self.id, "choice": "3"}
        payload_4 = {"poll": self.id, "choice": "4"}
        payload_5 = {"poll": self.id, "choice": "5"}
        self.client.post("/portal/options/", payload_1)
        self.client.post("/portal/options/", payload_2)
        self.client.post("/portal/options/", payload_3)
        self.client.post("/portal/options/", payload_4)
        self.client.post("/portal/options/", payload_5)
        self.assertEqual(5, PollOption.objects.all().count())
        # asserts options were created and were placed to right poll
        for poll_option in PollOption.objects.all():
            self.assertEqual(Poll.objects.get(id=self.id), poll_option.poll)
        response = self.client.get("/portal/polls/browse/")
        res_json = json.loads(response.content)
        self.assertEqual(5, len(res_json[0]["options"]))
        # adding more than 5 options to same poll should not be allowed
        payload_6 = {"poll": self.id, "choice": "6"}
        response = self.client.post("/portal/options/", payload_6)
        self.assertEqual(5, PollOption.objects.all().count())

    def test_edit_vote_view(self):
        response = self.client.get(f"/portal/polls/{self.id}/edit_view/")
        res_json = json.loads(response.content)
        self.assertEqual("Test Source 1", res_json["source"])
        # test that options key is in response
        self.assertIn("options", res_json)


class TestPollVotes(TestCase):
    """Tests Create/Update Polls and History"""

    def setUp(self):
        self.client = APIClient()
        self.target_id = TargetPopulation.objects.create(population="SEAS").id
        self.test_user = User.objects.create_user("user", "user@seas.upenn.edu", "user")
        self.client.force_authenticate(user=self.test_user)

        # creates 4 polls, each with 3 options
        # p1, p4 user is in target population
        self.poll_user = User.objects.create_user("poll_user", "poll_user@a.com", "poll_user")
        p1 = Poll.objects.create(
            user=self.poll_user,
            source="poll 1",
            question="poll question 1",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
        )
        p1.target_populations.add(self.target_id)
        p1.save()
        self.p1_id = p1.id
        p1_op1 = PollOption.objects.create(poll=p1, choice="choice 1")
        self.p1_op1_id = p1_op1.id
        PollOption.objects.create(poll=p1, choice="choice 2")
        p1_op3 = PollOption.objects.create(poll=p1, choice="choice 3")
        self.p1_op3_id = p1_op3.id
        p2 = Poll.objects.create(
            user=self.poll_user,
            source="poll 2",
            question="poll question 2",
            expire_date=timezone.now() + datetime.timedelta(days=2),
            approved=True,
        )
        self.p2_id = p2.id
        PollOption.objects.create(poll=p2, choice="choice 4")
        PollOption.objects.create(poll=p2, choice="choice 5")
        PollOption.objects.create(poll=p2, choice="choice 6")
        p3 = Poll.objects.create(
            user=self.poll_user,
            source="poll 3",
            question="poll question 3",
            expire_date=timezone.now() - datetime.timedelta(days=3),
            approved=True,
        )
        self.p3_id = p3.id
        PollOption.objects.create(poll=p3, choice="choice 7")
        PollOption.objects.create(poll=p3, choice="choice 8")
        PollOption.objects.create(poll=p3, choice="choice 9")
        p4 = Poll.objects.create(
            user=self.poll_user,
            source="poll 4",
            question="poll question 4",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
        )
        p4.target_populations.add(self.target_id)
        p4.save()
        self.p4_id = p4.id
        p4_op1 = PollOption.objects.create(poll=p4, choice="choice 10")
        self.p4_op1_id = p4_op1.id
        PollOption.objects.create(poll=p4, choice="choice 11")
        PollOption.objects.create(poll=p4, choice="choice 12")

    def test_create_vote(self):
        payload_1 = {"poll_options": [self.p1_op1_id]}
        response = self.client.post("/portal/votes/", payload_1)
        res_json = json.loads(response.content)
        # tests that voting works
        self.assertIn(self.p1_op1_id, res_json["poll_options"])
        self.assertEqual(1, PollVote.objects.all().count())
        self.assertEqual(self.test_user, PollVote.objects.all().first().user)

    def test_update_vote(self):
        payload_1 = {"poll_options": [self.p1_op1_id]}
        response_1 = self.client.post("/portal/votes/", payload_1)
        res_json_1 = json.loads(response_1.content)
        payload_2 = {"poll_options": [self.p1_op3_id]}
        response_2 = self.client.patch(f'/portal/votes/{res_json_1["id"]}/', payload_2)
        res_json_2 = json.loads(response_2.content)
        # test that updating vote works
        self.assertIn(self.p1_op3_id, res_json_2["poll_options"])
        self.assertEqual(1, PollVote.objects.all().count())
        self.assertEqual(self.test_user, PollVote.objects.all().first().user)

    def test_history(self):
        payload_1 = {"poll_options": [self.p1_op1_id]}
        self.client.post("/portal/votes/", payload_1)
        response = self.client.get(reverse("portal:poll-history-list"))
        res_json = json.loads(response.content)
        # asserts that history works, can see expired posts and posts that
        # user voted for
        # also asserts that data collection works
        self.assertEqual(3, len(res_json[0]["poll"]["options"]))
        self.assertEqual(3, len(res_json[1]["poll"]["options"]))

    def test_recent_poll_empty(self):
        response = self.client.get(reverse("portal:poll-history-recent"))
        res_json = json.loads(response.content)
        # recent polls returns default empty poll
        self.assertEquals(None, res_json["created_date"])
        self.assertEquals(None, res_json["poll"]["created_date"])

    def test_recent_poll(self):
        # answer poll
        payload_1 = {"poll_options": [self.p1_op1_id]}
        self.client.post("/portal/votes/", payload_1)
        response = self.client.get(reverse("portal:poll-history-recent"))
        res_json = json.loads(response.content)
        # assert that payload1 poll answered is most recent
        self.assertEquals(self.p1_id, res_json["poll"]["id"])
        # answer another poll
        payload_2 = {"poll_options": [self.p4_op1_id]}
        self.client.post("/portal/votes/", payload_2)
        response2 = self.client.get(reverse("portal:poll-history-recent"))
        res_json2 = json.loads(response2.content)
        # assert newly answered poll is most recent
        self.assertEquals(self.p4_id, res_json2["poll"]["id"])

    def test_polls_status(self):
        Poll.objects.create(
            user=self.test_user,
            source="awaiting approval",
            question="hey?",
            start_date=timezone.localtime(),
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
            approved=False,
            multiselect=True,
            user_comment="",
            admin_comment="",
        )

        Poll.objects.create(
            user=self.test_user,
            source="revision",
            question="hey?",
            start_date=timezone.localtime(),
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
            approved=False,
            multiselect=True,
            user_comment="",
            admin_comment="need revision",
        )

        Poll.objects.create(
            user=self.test_user,
            source="approved",
            question="hey?",
            start_date=timezone.localtime(),
            expire_date=timezone.localtime() + datetime.timedelta(days=1),
            approved=True,
            multiselect=True,
            user_comment="",
        )
        response = self.client.get("/portal/polls/status/")
        res_json = json.loads(response.content)
        self.assertEqual(3, len(res_json))

        approved = res_json["approved"]
        self.assertEqual(1, len(approved))
        self.assertEqual("approved", approved[0]["source"])

        awaiting = res_json["awaiting_approval"]
        self.assertEqual(1, len(awaiting))
        self.assertEqual("awaiting approval", awaiting[0]["source"])

        revision = res_json["revision"]
        self.assertEqual(1, len(revision))
        self.assertEqual("revision", revision[0]["source"])
