from django.contrib.auth import get_user_model
from django.test import TestCase
from gsr_booking.models import Group, GroupMembership, UserSearchIndex
from rest_framework.test import APIClient


User = get_user_model()


class UserViewTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", password="password", first_name="user", last_name="one"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password", first_name="user", last_name="two"
        )
        UserSearchIndex.objects.create(user=self.user1)
        UserSearchIndex.objects.create(user=self.user2)

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
        self.assertEqual(1, len(response.data["booking_groups"]))

    def test_me_user_detail_in_group(self):
        response = self.client.get("/users/me/")
        self.assertTrue(200, response.status_code)
        self.assertEqual(1, len(response.data["booking_groups"]))

    def test_user_detail_invited(self):
        self.group.members.add(self.user2)
        memship = self.group.memberships.all()[0]
        memship.accepted = False
        memship.save()
        response = self.client.get("/users/user2/")
        self.assertTrue(200, response.status_code)
        self.assertEqual(0, len(response.data["booking_groups"]))

    def test_user_invites(self):
        self.group.members.add(self.user2)
        memship = self.group.memberships.all()[0]
        memship.accepted = False
        memship.save()
        response = self.client.get("/users/user2/invites/")
        self.assertTrue(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_actualize_nouser_invite(self):
        mem = GroupMembership.objects.create(username="user4", group=self.group, accepted=False)
        self.assertTrue(mem.user is None)

        user4 = User.objects.create_user(username="user4", password="password")
        self.client.logout()
        self.client.login(username="user4", password="password")
        response = self.client.post("/users/user4/activate/")
        self.assertEqual(200, response.status_code)
        mem = GroupMembership.objects.get(pk=mem.pk)
        self.assertEqual(user4, mem.user)
        self.assertEqual("user4", mem.username)

    def test_search_users_first_name(self):
        response = self.client.get("/users/search/", {"q": "user"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_search_users_full_name(self):
        response = self.client.get("/users/search/", {"q": "user one"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_search_users_pennkey(self):
        response = self.client.get("/users/search/", {"q": "user1"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))


class MembershipViewTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self.group = Group.objects.create(owner=self.user1, name="g1", color="blue")
        self.group2 = Group.objects.create(owner=self.user2, name="g2", color="white")
        self.client = APIClient()
        self.client.login(username="user1", password="password")

    def test_invite_single(self):
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            GroupMembership.objects.filter(
                group=self.group.pk, accepted=False, user=self.user2
            ).exists()
        )

    def test_bulk_invite(self):
        User.objects.create_user(username="user3", password="password")
        response = self.client.post(
            "/membership/invite/", {"user": "user2,user3", "group": self.group.pk}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            2, GroupMembership.objects.filter(accepted=False).count(), GroupMembership.objects.all()
        )

    def test_invite_by_pennkey_no_user(self):
        response = self.client.post(
            f"/membership/invite/", {"user": "user4", "group": self.group.pk}
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            GroupMembership.objects.filter(
                group=self.group.pk, accepted=False, user=None, username="user4"
            ).exists()
        )

    def test_invite_no_permission(self):
        self.client.login(username="user2", password="password")
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(403, response.status_code)

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
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(400, response.status_code)

    def test_already_member_invite_fails(self):
        GroupMembership.objects.create(user=self.user2, group=self.group, accepted=True)
        response = self.client.post(
            "/membership/invite/", {"user": "user2", "group": self.group.pk}
        )
        self.assertEqual(400, response.status_code)

    def test_accept_invite(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.post(f"/membership/{mem.pk}/accept/")
        self.assertEqual(200, response.status_code)
        self.assertTrue(GroupMembership.objects.get(pk=mem.pk).accepted)

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

    def test_accept_invite_no_user_fails(self):
        mem = GroupMembership.objects.create(username="user4", group=self.group2, accepted=True)
        response = self.client.post(f"/membership/{mem.pk}/accept/")
        self.assertEqual(404, response.status_code)

    def test_decline_invite(self):
        mem = GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.post(f"/membership/{mem.pk}/decline/")
        self.assertEqual(200, response.status_code)
        self.assertFalse(GroupMembership.objects.filter(pk=mem.pk).exists())

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


class GroupTestCase(TestCase):
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
        self.assertEqual(1, len(response.data))

    def test_get_groups_includes_invites(self):
        GroupMembership.objects.create(user=self.user1, group=self.group2, accepted=False)
        response = self.client.get(f"/groups/{self.group2.pk}/")
        self.assertEqual(200, response.status_code)

    def test_get_group_not_involved_fails(self):
        response = self.client.get(f"/groups/{self.group2.pk}/")
        self.assertEqual(404, response.status_code)

    def test_make_group(self):
        response = self.client.post(f"/groups/", {"name": "gx", "color": "blue"})
        self.assertEqual(201, response.status_code, response.data)
        self.assertEqual(3, Group.objects.count())
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

    #TODO: Curently this test fails, due to querydict not immutable error
    # def test_book_room(self):
    #     GroupMembership.objects.create(user=self.user1, group=self.group, accepted=True)
    #     GroupMembership.objects.create(user=self.user2, group=self.group, accepted=True)
    #     params = {"room": 16993, "start": "2020-03-10T10:00:00-0500", "end": "2020-03-10T16:00:00-0500", "lid": 2587}
    #     response = self.client.post(f"/groups/{self.group.pk}/book-room/", params)
    #     self.assertEqual(200, response.status_code)
