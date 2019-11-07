from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    group = models.ForeignKey('Group', on_delete=models.CASCADE)

    # when accepted if False, this is a request. when accepted is True, this is an active membership.
    accepted = models.BooleanField(default=False)

    ADMIN = 'A'
    MEMBER = 'M'
    type = models.CharField(max_length=10, choices=[(ADMIN, 'Admin'), (MEMBER, 'M')])

    def __str__(self):
        return '{}<->{}'.format(self.user, self.group)


class Group(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through=GroupMembership, related_name='booking_groups')

    name = models.CharField(max_length=255)
    color = models.CharField(max_length=8)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {}'.format(self.pk, self.name)
