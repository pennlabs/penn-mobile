from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from gsr_booking.models import Group, GroupMembership


def check_wharton(*args):
    return False


User = get_user_model()

"""
class UserViewTestCase(TestCase):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", password="password", first_name="user", last_name="one"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password", first_name="user", last_name="two"
        )

        self.group = Group.objects.create(owner=self.user1, name="g1", color="blue")
        self.group.members.add(self.user1)
        memship = self.group.memberships.all()[0]
        memship.accepted = True
        memship.save()
        self.client = APIClient()
        self.client.login(username="user1", password="password")

    def test_user_list(self):
        response = self.client.get("/users/")
        self.assertTrue(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_user_detail_in_group(self):
        response = self.client.get("/users/user1/")
        self.assertTrue(200, response.status_code)
        self.assertEqual(2, len(response.data["booking_groups"]))

    def test_me_user_detail_in_group(self):
        response = self.client.get("/users/me/")
        self.assertTrue(200, response.status_code)
        self.assertEqual(2, len(response.data["booking_groups"]))

    def test_user_detail_invited(self):
        self.group.members.add(self.user2)
        memship = self.group.memberships.all()[0]
        memship.accepted = False
        memship.save()
        response = self.client.get("/users/user2/")
        self.assertTrue(200, response.status_code)
        self.assertEqual(1, len(response.data["booking_groups"]))

    def test_user_invites(self):
        self.group.members.add(self.user2)
        memship = self.group.memberships.all()[0]
        memship.accepted = False
        memship.save()
        response = self.client.get("/users/user2/invites/")
        self.assertTrue(200, response.status_code)
        self.assertEqual(1, len(response.data))
"""


class MembershipViewTestCase(TestCase):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self.group = Group.objects.create(owner=self.user1, name="g1", color="blue")
        self.group2 = Group.objects.create(owner=self.user2, name="g2", color="white")
        self.client = APIClient()
        self.client.login(username="user1", password="password")

    def test_invite_single(self):
        self.client.login(username="user2", password="password")
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(200, response.status_code)

    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def test_bulk_invite(self):
        User.objects.create_user(username="user3", password="password")
        self.client.login(username="user2", password="password")
        response = self.client.post(
            "/membership/invite/", {"user": "user2,user3", "group": self.group.pk}
        )
        self.assertEqual(200, response.status_code)

    def test_invite_no_permission(self):
        self.client.login(username="user2", password="password")
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(200, response.status_code)

    def test_invite_logged_out_fails(self):
        self.client.logout()
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(403, response.status_code)

    def test_invite_bad_group_fails(self):
        response = self.client.post("/membership/invite/", {"user": "user2", "group": 300})
        self.assertEqual(404, response.status_code)

    def test_duplicate_invite_fails(self):
        GroupMembership.objects.create(user=self.user2, group=self.group, accepted=False)
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(403, response.status_code)

    def test_already_member_invite_fails(self):
        GroupMembership.objects.create(user=self.user2, group=self.group, accepted=True)
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(403, response.status_code)

    def test_accept_invite(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.post(f"/membership/{mem.pk}/accept/")
        self.assertEqual(200, response.status_code)
        self.assertTrue(GroupMembership.objects.get(pk=mem.pk).accepted)

    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def test_wrong_user_accept_invite_fails(self):
        user3 = User.objects.create_user(username="user3", password="password")
        mem = GroupMembership.objects.create(user=user3, group=self.group2, accepted=False)
        response = self.client.post(f"/membership/{mem.pk}/accept/")
        self.assertEqual(403, response.status_code)
        self.assertFalse(GroupMembership.objects.get(pk=mem.pk).accepted)

    def test_accept_invite_again_fails(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=True)
        response = self.client.post(f"/membership/{mem.pk}/accept/")
        self.assertEqual(404, response.status_code)

    def test_decline_invite(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.post(f"/membership/{mem.pk}/decline/")
        self.assertEqual(200, response.status_code)
        self.assertFalse(GroupMembership.objects.filter(pk=mem.pk).exists())

    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def test_wrong_user_decline_invite_fails(self):
        user3 = User.objects.create_user(username="user3", password="password")
        mem = GroupMembership.objects.create(user=user3, group=self.group2, accepted=False)
        response = self.client.post(f"/membership/{mem.pk}/decline/")
        self.assertEqual(403, response.status_code)
        self.assertTrue(GroupMembership.objects.filter(pk=mem.pk).exists())
        self.assertFalse(GroupMembership.objects.get(pk=mem.pk).accepted)

    def test_decline_invite_again_fails(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=True)
        response = self.client.post(f"/membership/{mem.pk}/decline/")
        self.assertEqual(404, response.status_code)

    def test_promote_to_admin(self):
        GroupMembership.objects.create(user=self.user1, group=self.group, accepted=True, type="A")
        mem = GroupMembership.objects.create(
            user=self.user2, group=self.group, accepted=True, type="M"
        )
        response = self.client.patch(f"/membership/{mem.pk}/", {"type": "A"})
        self.assertEqual(200, response.status_code)
        mem.refresh_from_db()
        self.assertEqual("A", mem.type)


class GroupTestCase(TestCase):
    @mock.patch("gsr_booking.models.GroupMembership.check_wharton", check_wharton)
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self.group = Group.objects.create(owner=self.user1, name="g1", color="blue")
        self.group2 = Group.objects.create(owner=self.user2, name="g2", color="white")
        self.client = APIClient()
        self.client.login(username="user1", password="password")

    def test_get_groups(self):
        response = self.client.get("/groups/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_get_groups_includes_invites(self):
        GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.get(f"/groups/{self.group2.pk}/")
        self.assertEqual(200, response.status_code)

    def test_get_group_not_involved_fails(self):
        response = self.client.get(f"/groups/{self.group2.pk}/")
        self.assertEqual(404, response.status_code)

    def test_make_group(self):
        response = self.client.post("/groups/", {"name": "gx", "color": "blue"})
        self.assertEqual(201, response.status_code, response.data)
        self.assertEqual(5, Group.objects.count())
        self.assertEqual("user1", Group.objects.get(name="gx").owner.username)

    def test_only_accepted_memberships(self):
        gm = GroupMembership.objects.create(user=self.user2, group=self.group, accepted=False)
        response = self.client.get(f"/groups/{self.group.pk}/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data["memberships"]))
        gm.accepted = True
        gm.save()
        response = self.client.get(f"/groups/{self.group.pk}/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data["memberships"]))

    def test_book_rooms(self):
        GroupMembership.objects.create(user=self.user1, group=self.group, accepted=True)
        GroupMembership.objects.create(user=self.user2, group=self.group, accepted=True)
        params = {
            "room_bookings": [
                {
                    "room": 16993,
                    "start": "2020-03-10T10:00:00-0500",
                    "end": "2020-03-10T16:00:00-0500",
                    "lid": 2587,
                }
            ]
        }
        response = self.client.post(f"/groups/{self.group.pk}/book-rooms/", params, format="json")
        self.assertEqual(200, response.status_code)

    def test_book_rooms_forbidden_if_not_admin(self):
        # where user2 is logged in
        self.client.login(username="user2", password="password")
        GroupMembership.objects.create(user=self.user1, group=self.group, accepted=True)
        GroupMembership.objects.create(user=self.user2, group=self.group, accepted=True, type="M")
        params = {
            "room_bookings": [
                {
                    "room": 16993,
                    "start": "2020-03-10T10:00:00-0500",
                    "end": "2020-03-10T16:00:00-0500",
                    "lid": 2587,
                }
            ]
        }
        response = self.client.post(f"/groups/{self.group.pk}/book-rooms/", params, format="json")
        self.assertEqual(403, response.status_code)

    def test_book_rooms_forbidden_if_not_member(self):
        # where user2 is logged in
        self.client.login(username="user2", password="password")
        GroupMembership.objects.create(user=self.user1, group=self.group, accepted=True)
        params = {
            "room_bookings": [
                {
                    "room": 16993,
                    "start": "2020-03-10T10:00:00-0500",
                    "end": "2020-03-10T16:00:00-0500",
                    "lid": 2587,
                }
            ]
        }
        response = self.client.post(f"/groups/{self.group.pk}/book-rooms/", params, format="json")
        self.assertEqual(403, response.status_code)

    def test_book_rooms_group_does_not_exist(self):
        GroupMembership.objects.create(user=self.user1, group=self.group, accepted=True)
        GroupMembership.objects.create(user=self.user2, group=self.group, accepted=True, type="M")
        params = {
            "room_bookings": [
                {
                    "room": 16993,
                    "start": "2020-03-10T10:00:00-0500",
                    "end": "2020-03-10T16:00:00-0500",
                    "lid": 2587,
                }
            ]
        }
        response = self.client.post(f"/groups/{-1}/book-rooms/", params, format="json")
        self.assertEqual(404, response.status_code)
