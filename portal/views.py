from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from portal.models import Poll, PollOption, PollVote
from portal.serializers import (
    AdminPollSerializer,
    CreatePollVoteSerializer,
    PollOptionSerializer,
    RetrievePollSerializer,
    RetrievePollVoteSerializer,
    UserPollSerializer,
)


class RetrievePolls(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Poll.objects.all()
    serializer_class = RetrievePollSerializer

    @action(detail=False, methods=["get"])
    def browse(self, request):
        polls_available = Poll.objects.filter(expire_date__gte=timezone.localtime(), approved=True)
        polls_answered = PollVote.objects.filter(poll__in=polls_available).values_list(
            "poll", flat=True
        )
        return Response(
            self.serializer_class(polls_available.exclude(id__in=polls_answered), many=True).data
        )

    @action(detail=False, methods=["get"])
    def review(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied()
        return Response(self.serializer_class(Poll.objects.filter(approved=False), many=True).data)


# FIX THIS
# MAKE IT RETURN HISTORY IN ORDER + DATA ON USER IF IT'S THERE
class RetrievePollVotes(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RetrievePollVoteSerializer

    def get_queryset(self):
        return PollVote.objects.filter()


# COMBINE THESE INTO ONE GENERIC
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


class UpdatePollOption(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PollOptionSerializer

    def get_queryset(self):
        return PollOption.objects.filter(user=self.request.user)


class CreatePollVote(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreatePollVoteSerializer


class UpdatePollVote(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreatePollVoteSerializer

    def get_queryset(self):
        return PollVote.objects.filter(user=self.request.user)
