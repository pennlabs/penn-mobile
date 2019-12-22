from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from gsr_booking.models import Group, GroupMembership
User = get_user_model()


class UserViewTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.group = Group.objects.create(owner=self.user1, name='g1', color='blue')
        self.group.members.add(self.user1)
        memship = self.group.groupmembership_set.all()[0]
        memship.accepted = True
        memship.save()
        self.client = APIClient()
        self.client.login(username='user1', password='password')

    def test_user_list(self):
        response = self.client.get('/users/')
        self.assertTrue(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_user_detail_in_group(self):
        response = self.client.get('/users/user1/')
        self.assertTrue(200, response.status_code)
        self.assertEqual(1, len(response.data['booking_groups']))

    def test_user_detail_invited(self):
        self.group.members.add(self.user2)
        memship = self.group.groupmembership_set.all()[0]
        memship.accepted = False
        memship.save()
        response = self.client.get('/users/user2/')
        self.assertTrue(200, response.status_code)
        self.assertEqual(0, len(response.data['booking_groups']))

    def test_user_invites(self):
        self.group.members.add(self.user2)
        memship = self.group.groupmembership_set.all()[0]
        memship.accepted = False
        memship.save()
        response = self.client.get('/users/user2/invites/')
        self.assertTrue(200, response.status_code)
        self.assertEqual(1, len(response.data))


class MembershipViewTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.group = Group.objects.create(owner=self.user1, name='g1', color='blue')
        self.client = APIClient()

    def test_invite_single(self):
        response = self.client.post('/membership/invite/', {'user': 'user2', 'group': self.group.pk})
        self.assertEqual(200, response.status_code)
        self.assertTrue(GroupMembership.objects.filter(group=self.group.pk,
                                                       user=self.user2).exists())

    def test_bulk_invite(self):
        user3 = User.objects.create_user(username='user3', password='password')
        response = self.client.post('/membership/invite/',
                                    {
                                        'user': 'user2,user3',
                                        'group': self.group.pk
                                    })
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, GroupMembership.objects.filter(accepted=False).count(), GroupMembership.objects.all())
