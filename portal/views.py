from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from portal.models import Poll, PollOption, PollVote
from portal.serializers import (
    AdminPollSerializer,
    CreateUpdatePollVoteSerializer,
    PollOptionSerializer,
    RetrievePollSerializer,
    RetrievePollVoteSerializer,
    UserPollSerializer,
)


class RetrievePolls(viewsets.ReadOnlyModelViewSet):
    """Viewset for browsing polls for user, and reviewing polls for admins"""

    permission_classes = [IsAuthenticated]
    queryset = Poll.objects.all()
    serializer_class = RetrievePollSerializer
    

    @action(detail=False, methods=["get"])
    def browse(self, request):
        # filters for all possible available polls, then filters for all polls answered
        # by user, and finally returns the difference in poll sets
        polls_available = Poll.objects.filter(expire_date__gte=timezone.localtime(), approved=True)
        polls_answered = PollVote.objects.filter(
            user=request.user, poll__in=polls_available
        ).values_list("poll", flat=True)
        return Response(
            self.serializer_class(polls_available.exclude(id__in=polls_answered), many=True).data
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def review(self, request):
        # returns list of polls that still need to be approved
        return Response(self.serializer_class(Poll.objects.filter(approved=False), many=True).data)


class RetrievePollVotes(APIView):
    """Retrieve history of polls and their statistics"""

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # filters for all polls that user voted in
        serializer = RetrievePollVoteSerializer(
            PollVote.objects.filter(user=request.user), many=True
        )
        history_list = serializer.data
        # filters for all polls user has not voted in
        remaining_list = RetrievePollSerializer(
            Poll.objects.filter(expire_date__lte=timezone.localtime()).exclude(
                id__in=PollVote.objects.filter(user=request.user).values_list("poll", flat=True),
                approved=True,
            ),
            many=True,
        ).data
        # puts remaining_list in the same format of history_list, then appends them
        for entry in remaining_list:
            context = {"id": entry["id"], "poll": entry, "poll_option": {}}
            history_list.append(context)
        # calculates statistics for each poll
        for entry in history_list:
            context = {"poll_statistics": self.calculate_statistics(entry["poll"]["id"])}  # stat
            entry.update(context)
        return Response(sorted(history_list, key=lambda i: i["poll"]["expire_date"], reverse=True))

    def calculate_statistics(self, id):
        """Returns the statistics of school and year for each poll"""
        poll = Poll.objects.get(id=id)
        options = PollOption.objects.filter(poll=poll)
        statistic_list = []
        # loops through each option and aggregates votes
        for option in options:
            votes = PollVote.objects.filter(poll_option=option)
            context = {"schools": {}, "years": {}}
            for vote in votes:
                year = 2024  # arbitrary for now, don't know how to get this yet
                school = self.get_affiliation(vote.user.email)
                if year not in context["years"].keys():
                    context["years"][year] = 1
                else:
                    context["years"][year] += 1
                if school not in context["schools"].keys():
                    context["schools"][school] = 1
                else:
                    context["schools"][school] += 1
            statistic_list.append({option.choice: context})
        return statistic_list

    def get_affiliation(self, email):
        """Gets the school based on user's email"""

        if "wharton" in email:
            return "Wharton"
        elif "seas" in email:
            return "SEAS"
        elif "sas" in email:
            return "SAS"
        elif "nursing" in email:
            return "Nursing"
        else:
            return "Other"


class CreatePoll(generics.CreateAPIView):
    """Creates a Poll"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserPollSerializer


class UpdatePoll(generics.UpdateAPIView):
    """Updates a Poll, only admin or user that created poll can update"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Returns different serializer based on user status"""
        if self.request.user.is_superuser:
            return AdminPollSerializer
        else:
            return UserPollSerializer

    def get_queryset(self):
        return Poll.objects.all()


class CreatePollOptions(generics.CreateAPIView):
    """Creates Poll Options for a poll"""

    serializer_class = PollOptionSerializer

    def get_serializer(self, *args, **kwargs):
        # bulk creates options
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super(CreatePollOptions, self).get_serializer(*args, **kwargs)


class UpdatePollOption(generics.UpdateAPIView):
    """Updates Poll Option. Only user that created poll can edit this"""

    permission_classes = [IsAuthenticated]
    serializer_class = PollOptionSerializer

    def get_queryset(self):
        return PollOption.objects.all()


class CreatePollVote(generics.CreateAPIView):
    """Used to cast vote, can only vote once"""

    permission_classes = [IsAuthenticated]
    serializer_class = CreateUpdatePollVoteSerializer


class UpdatePollVote(generics.UpdateAPIView):
    """Used to update vote, only user that voted can adjust vote"""

    permission_classes = [IsAuthenticated]
    serializer_class = CreateUpdatePollVoteSerializer

    def get_queryset(self):
        return PollVote.objects.filter(user=self.request.user)
