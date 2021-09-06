from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from portal.models import Poll, PollOption, PollVote
from portal.serializers import (
    PollOptionSerializer,
    PollSerializer,
    PollVoteSerializer,
    RetrievePollSerializer,
    RetrievePollVoteSerializer,
)


class Polls(viewsets.ModelViewSet):
    """
    browse:
    returns a list of Polls that are valid and
    haven't been filled out by user

    review:
    returns a list of unapproved Polls for admin

    create:
    Create a Poll

    partial_update:
    Update certain fields in the Poll.
    Only user who creates Poll can edit it

    destroy:
    Delete a Poll.
    """

    permission_classes = [IsAuthenticated]
    queryset = Poll.objects.all()

    def get_serializer_class(self):
        if self.action in ["browse", "review"]:
            return RetrievePollSerializer
        else:
            return PollSerializer

    def get_queryset(self):
        if self.action == "browse":
            # return list of votes that haven't been answered
            # by user, and that are valid
            return Poll.objects.filter(
                ~Q(id__in=PollVote.objects.filter(user=self.request.user).values_list("poll_id")),
                expire_date__gte=timezone.localtime(),
                approved=True,
            )
        elif self.action == "review":
            # return list of polls that need to be approved
            return Poll.objects.filter(approved=False)
        elif self.action == "partial_update":
            # if user is admin, they can update anything
            # if user is not admin, they can only update their own polls
            if self.request.user.is_superuser:
                return Poll.objects.all()
            else:
                return Poll.objects.filter(user=self.request.user)
        elif self.action == "destroy":
            if self.request.user.is_superuser:
                return Poll.objects.all()
        return None

    @action(detail=False, methods=["get"])
    def browse(self, request):
        return super().list(request)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def review(self, request):
        return super().list(request)


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
            context = {"id": None, "poll": entry, "poll_option": {}}
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


class PollOptions(viewsets.ModelViewSet):
    """
    create:
    Create a Poll Option.

    partial_update:
    Update certain fields in the membership.
    Only specify the fields that you want to change.

    destroy:
    Delete a Poll Option.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PollOptionSerializer
    queryset = PollOption.objects.all()

    def get_queryset(self):
        # if user is admin, they can update anything
        # if user is not admin, they can only update their own options
        if self.request.user.is_superuser:
            return PollOption.objects.all()
        else:
            return PollOption.objects.filter(poll__in=Poll.objects.filter(user=self.request.user))


class PollVotes(viewsets.ModelViewSet):
    """
    create:
    Create a Poll Vote.

    partial_update:
    Update certain fields in the Poll Vote.
    Only specify the fields that you want to change.

    destroy:
    Delete a Poll Vote.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PollVoteSerializer
    queryset = PollVote.objects.all()

    def get_queryset(self):
        # if user is admin, they can update anything
        # if user is not admin, they can only update their own polls
        if self.request.user.is_superuser:
            return PollVote.objects.all()
        else:
            return PollVote.objects.filter(user=self.request.user)
