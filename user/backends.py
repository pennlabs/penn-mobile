from accounts.backends import LabsUserBackend

from user.models import Profile


class MobileBackend(LabsUserBackend):
    """
    A custom DLA backend that creates Profile object for user on user creation.
    """

    def post_authenticate(self, user, created, dictionary):
        if created:
            Profile.objects.create(user=user)
            user.save()
