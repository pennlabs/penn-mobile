from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class GroupMembership(models.Model):
    # INVARIANT: either user or username should always be set. if user is not None, then the
    # username should the be username of the associated user.
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships", blank=True, null=True
    )
    username = models.CharField(max_length=127, blank=True, null=True, default=None)

    group = models.ForeignKey("Group", on_delete=models.CASCADE)

    # When accepted is False, this is a request, otherwise this is an active membership.
    accepted = models.BooleanField(default=False)

    ADMIN = "A"
    MEMBER = "M"
    type = models.CharField(max_length=10, choices=[(ADMIN, "Admin"), (MEMBER, "M")])

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


class Group(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through=GroupMembership, related_name="booking_groups")

    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}: {}".format(self.pk, self.name)

    def has_member(self, user):
        memberships = GroupMembership.objects.filter(group=self, accepted=True)
        return memberships.all().filter(user=user).exists()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        GroupMembership.objects.create(
            group=self, user=self.owner, type=GroupMembership.ADMIN, accepted=True
        )


class UserSearchIndex(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, db_index=True)
    pennkey = models.CharField(max_length=255, db_index=True)

    def save(self, *args, **kwargs):
        self.full_name = f"{self.user.first_name} {self.user.last_name}"
        self.pennkey = self.user.username
        super().save(*args, **kwargs)


# Model to store credentials necessary for booking GSRs.
class GSRBookingCredentials(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Session ID is used for Wharton GSR booking
    session_id = models.CharField("session ID", max_length=50, unique=True, null=True)

    # Expiration date of the Session ID
    expiration_date = models.DateTimeField("session ID expiration date")

    # When Session ID was added
    date_added = models.DateTimeField("date added (Session ID)", auto_now_add=True)

    # For LibCal, school emails are used instead
    email = models.CharField("school email", max_length=255, unique=True, null=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "GSR Booking Credentials"
        verbose_name_plural = "GSR Booking Credentials"