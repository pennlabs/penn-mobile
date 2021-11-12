from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class GroupMembership(models.Model):
    # INVARIANT: either user or username should always be set. if user is not None, then the
    # username should the be username of the associated user.
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships", blank=True, null=True,
    )
    username = models.CharField(max_length=127, blank=True, null=True, default=None)

    group = models.ForeignKey("Group", on_delete=models.CASCADE, related_name="memberships")

    # When accepted is False, this is a request, otherwise this is an active membership.
    accepted = models.BooleanField(default=False)

    ADMIN = "A"
    MEMBER = "M"
    type = models.CharField(max_length=10, choices=[(ADMIN, "Admin"), (MEMBER, "Member")])

    pennkey_allow = models.BooleanField(default=False)

    notifications = models.BooleanField(default=True)

    @property
    def is_invite(self):
        return not self.accepted

    def __str__(self):
        return "{}<->{}".format(self.user, self.group)

    def save(self, *args, **kwargs):
        if self.user is not None:
            self.username = self.user.username
        elif (
            self.username is not None
        ):  # if no user has been set yet, try to find a user to attach.
            try:
                self.user = User.objects.get(username=self.username)
            except User.DoesNotExist:
                self.user = None
        else:  # Both user and username are None, which is an invalid Membership.
            raise ValueError("Either user or username must be set.")

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Group Membership"


class Group(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through=GroupMembership, related_name="booking_groups")

    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ADMIN = "A"
    MEMBER = "M"

    def __str__(self):
        return "{}: {}".format(self.pk, self.name)

    def has_member(self, user):
        memberships = GroupMembership.objects.filter(group=self, accepted=True)
        return memberships.all().filter(user=user).exists()

    def has_admin(self, user):
        memberships = GroupMembership.objects.filter(group=self, accepted=True)
        return memberships.all().filter(type="A").filter(user=user).exists()

    def get_pennkey_active_members(self):
        memberships = GroupMembership.objects.filter(group=self, accepted=True)
        pennkey_active_members_list = (
            memberships.all().filter(pennkey_allow=True).all().values("username", "user__email")
        )
        return [member for member in pennkey_active_members_list]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        GroupMembership.objects.get_or_create(
            group=self, user=self.owner, type=GroupMembership.ADMIN, accepted=True
        )


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
    reminder_sent = models.BooleanField(default=False)
