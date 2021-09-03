from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from portal.models import Poll
from portal.serializers import (
    AdminPollSerializer,
    PollOptionSerializer,
    RetrievePollSerializer,
    UserPollSerializer,
)


class RetrievePolls(generics.ListAPIView):
    serializer_class = RetrievePollSerializer

    # filter based on important stuff
    def get_queryset(self):
        return Poll.objects.all()


class CreatePoll(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPollSerializer


class UpdatePoll(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return AdminPollSerializer
        else:
            return UserPollSerializer

    def get_queryset(self):
        return Poll.objects.filter(user=self.request.user)


class CreatePollOptions(generics.CreateAPIView):
    serializer_class = PollOptionSerializer

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super(CreatePollOptions, self).get_serializer(*args, **kwargs)


# go vote

# list polls with the data / whether voted or not
# approving / editing
