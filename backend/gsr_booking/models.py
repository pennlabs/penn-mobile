import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout

from pennmobile.utils.time_formatter import stringify_date


User = get_user_model()


class GroupMembership(models.Model):
    # INVARIANT: either user or username should always be set. if user is not None, then the
    # username should the be username of the associated user.
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships", blank=True, null=True,
    )
    group = models.ForeignKey("Group", on_delete=models.CASCADE, related_name="memberships")

    # When accepted is False, this is a request, otherwise this is an active membership.
    accepted = models.BooleanField(default=False)

    ADMIN = "A"
    MEMBER = "M"
    type = models.CharField(max_length=10, choices=[(ADMIN, "Admin"), (MEMBER, "Member")])

    pennkey_allow = models.BooleanField(default=False)
    notifications = models.BooleanField(default=True)
    is_wharton = models.BooleanField(blank=True, null=True, default=None)

    @property
    def is_invite(self):
        return not self.accepted

    def __str__(self):
        return f"{self.user}-{self.group}"

    def save(self, *args, **kwargs):
        # determines whether user is wharton or not
        if self.is_wharton is None:
            self.is_wharton = self.check_wharton()
        super().save(*args, **kwargs)

    def check_wharton(self):
        # not using api_wrapper.py to prevent circular dependency
        url = f"https://apps.wharton.upenn.edu/gsr/api/v1/{self.user.username}/privileges"
        try:
            response = requests.get(
                url, headers={"Authorization": f"Token {settings.WHARTON_TOKEN}"}
            ).json()
            if "type" in response:
                # check if user is wharton
                return response["type"] == "whartonMBA" or response["type"] == "whartonUGR"
            else:
                # accomodate for inconsistent responses
                return False
        except (ConnectTimeout, ReadTimeout, KeyError, ConnectionError):
            return None

    class Meta:
        verbose_name = "Group Membership"


class Group(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through=GroupMembership, related_name="booking_groups")

    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_member(self, user):
        return self.members.filter(user=user).exists()

    def has_admin(self, user):
        return self.memberships.filter(
            user=user, type=GroupMembership.ADMIN, accepted=True
        ).exists()

    def get_pennkey_active_members(self):
        return [
            member for member in self.memberships.filter(accepted=True, pennkey_allow=True).all()
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.memberships.get_or_create(user=self.owner, type=GroupMembership.ADMIN, accepted=True)

    def __str__(self):
        return f"{self.name}-{self.owner}"


class GSR(models.Model):
    KIND_WHARTON = "WHARTON"
    KIND_LIBCAL = "LIBCAL"
    KIND_OPTIONS = ((KIND_WHARTON, "Wharton"), (KIND_LIBCAL, "Libcal"))

    kind = models.CharField(max_length=7, choices=KIND_OPTIONS, default=KIND_LIBCAL)
    lid = models.CharField(max_length=255)
    gid = models.IntegerField(null=True)
    name = models.CharField(max_length=255)
    image_url = models.URLField()

    def __str__(self):
        return f"{self.lid}-{self.gid}"


class Reservation(models.Model):
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_cancelled = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)

    def __str__(self):
        name = self.creator.username
        start_date = stringify_date(self.start)
        end_date = stringify_date(self.end)
        return f"{name}-{self.group.name}-{start_date}-{end_date}-{self.gid}"


class GSRBooking(models.Model):
    # TODO: change to non-null after reservations are created for current bookings
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    booking_id = models.CharField(max_length=255, null=True, blank=True)
    gsr = models.ForeignKey(GSR, on_delete=models.CASCADE)
    room_id = models.IntegerField()
    room_name = models.CharField(max_length=255)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.room_name} {stringify_date(self.start)}-{stringify_date(self.end)}"
