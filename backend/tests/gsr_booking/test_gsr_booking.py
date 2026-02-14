from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from gsr_booking.models import Group, GroupMembership


User = get_user_model()


class MyMembershipViewTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", password="password", first_name="user", last_name="one"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password", first_name="user", last_name="two"
        )

        with mock.patch(
            "gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False
        ), mock.patch("gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False):
            Group.objects.create(
                owner=self.user1, name="g1", color="blue"
            )  # creating group also adds user
            group2 = Group.objects.create(owner=self.user2, name="g2", color="blue")
            GroupMembership.objects.create(user=self.user1, group=group2, accepted=True)
            group3 = Group.objects.create(owner=self.user2, name="g3", color="blue")
            GroupMembership.objects.create(user=self.user1, group=group3)
        self.client = APIClient()
        self.client.login(username="user1", password="password")

    def test_user_memberships(self):
        response = self.client.get("/gsr/mymemberships/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_user_invites(self):
        response = self.client.get("/gsr/mymemberships/invites/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))


class MembershipViewTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self._patcher_seas = mock.patch(
            "gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False
        )
        self._patcher_wharton = mock.patch(
            "gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False
        )
        self._patcher_seas.start()
        self._patcher_wharton.start()
        self.group = Group.objects.create(owner=self.user1, name="g1", color="blue")
        self.group2 = Group.objects.create(owner=self.user2, name="g2", color="white")
        self.client = APIClient()
        self.client.login(username="user1", password="password")

    def tearDown(self):
        self._patcher_seas.stop()
        self._patcher_wharton.stop()

    def test_invite_single(self):
        self.client.login(username="user2", password="password")
        response = self.client.post(
            "/gsr/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(200, response.status_code)

    def test_bulk_invite(self):
        User.objects.create_user(username="user3", password="password")
        self.client.login(username="user2", password="password")
        response = self.client.post(
            "/gsr/membership/invite/", {"user": "user2,user3", "group": self.group.pk}
        )
        self.assertEqual(200, response.status_code)

    def test_invite_logged_out_fails(self):
        self.client.logout()
        response = self.client.post(
            "/gsr/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(403, response.status_code)

    def test_invite_bad_group_fails(self):
        response = self.client.post("/gsr/membership/invite/", {"user": "user2", "group": 300})
        self.assertEqual(404, response.status_code)

    def test_duplicate_invite_fails(self):
        GroupMembership.objects.create(user=self.user2, group=self.group, accepted=False)
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            "/gsr/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(403, response.status_code)

    def test_already_member_invite_fails(self):
        GroupMembership.objects.create(user=self.user2, group=self.group, accepted=True)
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            "/gsr/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(403, response.status_code)

    def test_accept_invite(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.post(f"/gsr/membership/{mem.pk}/accept/")
        self.assertEqual(200, response.status_code)
        self.assertTrue(GroupMembership.objects.get(pk=mem.pk).accepted)

    def test_wrong_user_accept_invite_fails(self):
        user3 = User.objects.create_user(username="user3", password="password")
        mem = GroupMembership.objects.create(user=user3, group=self.group2, accepted=False)
        response = self.client.post(f"/gsr/membership/{mem.pk}/accept/")
        self.assertEqual(403, response.status_code)
        self.assertFalse(GroupMembership.objects.get(pk=mem.pk).accepted)

    def test_accept_invite_again_fails(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=True)
        response = self.client.post(f"/gsr/membership/{mem.pk}/accept/")
        self.assertEqual(404, response.status_code)

    def test_decline_invite(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.post(f"/gsr/membership/{mem.pk}/decline/")
        self.assertEqual(200, response.status_code)
        self.assertFalse(GroupMembership.objects.filter(pk=mem.pk).exists())

    def test_wrong_user_decline_invite_fails(self):
        user3 = User.objects.create_user(username="user3", password="password")
        mem = GroupMembership.objects.create(user=user3, group=self.group2, accepted=False)
        response = self.client.post(f"/gsr/membership/{mem.pk}/decline/")
        self.assertEqual(403, response.status_code)
        self.assertTrue(GroupMembership.objects.filter(pk=mem.pk).exists())
        self.assertFalse(GroupMembership.objects.get(pk=mem.pk).accepted)

    def test_decline_invite_again_fails(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=True)
        response = self.client.post(f"/gsr/membership/{mem.pk}/decline/")
        self.assertEqual(404, response.status_code)

    def test_promote_to_admin(self):
        GroupMembership.objects.create(user=self.user1, group=self.group, accepted=True, type="A")
        mem = GroupMembership.objects.create(
            user=self.user2, group=self.group, accepted=True, type="M"
        )
        response = self.client.patch(f"/gsr/membership/{mem.pk}/", {"type": "A"})
        self.assertEqual(200, response.status_code)
        mem.refresh_from_db()
        self.assertEqual("A", mem.type)


class GroupTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self._patcher_seas = mock.patch(
            "gsr_booking.models.PennGroupsGSRBooker.is_seas", return_value=False
        )
        self._patcher_wharton = mock.patch(
            "gsr_booking.models.WhartonGSRBooker.is_wharton", return_value=False
        )
        self._patcher_seas.start()
        self._patcher_wharton.start()
        self.group = Group.objects.create(owner=self.user1, name="g1", color="blue")
        self.group2 = Group.objects.create(owner=self.user2, name="g2", color="white")
        self.client = APIClient()
        self.client.login(username="user1", password="password")

    def tearDown(self):
        self._patcher_seas.stop()
        self._patcher_wharton.stop()

    def test_get_groups(self):
        response = self.client.get("/gsr/groups/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_get_groups_includes_invites(self):
        GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.get(f"/gsr/groups/{self.group2.pk}/")
        self.assertEqual(200, response.status_code)

    def test_get_group_not_involved_fails(self):
        response = self.client.get(f"/gsr/groups/{self.group2.pk}/")
        self.assertEqual(404, response.status_code)

    def test_make_group(self):
        response = self.client.post("/gsr/groups/", {"name": "gx", "color": "blue"})
        self.assertEqual(201, response.status_code, response.data)
        self.assertEqual(3, Group.objects.count())
        self.assertEqual("user1", Group.objects.get(name="gx").owner.username)

    def test_only_accepted_memberships(self):
        gm = GroupMembership.objects.create(user=self.user2, group=self.group, accepted=False)
        response = self.client.get(f"/gsr/groups/{self.group.pk}/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data["memberships"]))
        gm.accepted = True
        gm.save()
        response = self.client.get(f"/gsr/groups/{self.group.pk}/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data["memberships"]))
