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
        return f"{self.user}<->{self.group}"

    def save(self, *args, **kwargs):
        # determines whether user is wharton or not
        if self.is_wharton is None:
            self.is_wharton = self.check_wharton()
        super().save(*args, **kwargs)

    def check_wharton(self):
        return WhartonGSRBooker.is_wharton(self.user)

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
        return f"{self.name}-{self.pk}"

    def has_member(self, user):
        memberships = GroupMembership.objects.filter(group=self, user=user)
        return memberships.all().exists()

    def has_admin(self, user):
        memberships = GroupMembership.objects.filter(group=self, accepted=True)
        return memberships.all().filter(type="A").filter(user=user).exists()

    def get_pennkey_active_members(self):
        memberships = GroupMembership.objects.filter(group=self, accepted=True)
        pennkey_active_members_list = memberships.all().filter(pennkey_allow=True).all()
        return [member for member in pennkey_active_members_list]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        GroupMembership.objects.get_or_create(
            group=self, user=self.owner, type=GroupMembership.ADMIN, accepted=True
        )


class GSRManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(in_use=True)


class GSR(models.Model):

    KIND_WHARTON = "WHARTON"
    KIND_LIBCAL = "LIBCAL"
    KIND_OPTIONS = ((KIND_WHARTON, "Wharton"), (KIND_LIBCAL, "Libcal"))

    kind = models.CharField(max_length=7, choices=KIND_OPTIONS, default=KIND_LIBCAL)
    lid = models.CharField(max_length=255)
    gid = models.IntegerField(null=True)
    name = models.CharField(max_length=255)
    image_url = models.URLField()

    in_use = models.BooleanField(default=True)

    objects = GSRManager()
    all_objects = models.Manager()  # for admin page

    def __str__(self):
        return f"{self.name}: {self.lid}-{self.gid}"


class Reservation(models.Model):
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)


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
        return f"{self.user} - {self.gsr.name} - {self.start} - {self.end}"


# import at end to prevent circular dependency
from gsr_booking.api_wrapper import WhartonGSRBooker  # noqa: E402
