from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from portal.logic import get_affiliation
from portal.models import Poll, PollOption, PollVote, TargetPopulation
from portal.serializers import (
    PollOptionSerializer,
    PollSerializer,
    PollVoteSerializer,
    RetrievePollSerializer,
    RetrievePollVoteSerializer,
    TargetPopulationSerializer,
)


class TargetPopulations(generics.ListAPIView):
    serializer_class = TargetPopulationSerializer
    queryset = TargetPopulation.objects.all()


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
    serializer_class = PollSerializer

    def get_queryset(self):
        return (
            Poll.objects.all()
            if self.request.user.is_superuser
            else Poll.objects.filter(user=self.request.user)
        )

    @action(detail=False, methods=["get"])
    def browse(self, request):
        # filters to see if user belongs to target population, either school or graduation year
        school = get_affiliation(request.user.email)
        school_id = (
            TargetPopulation.objects.get(population=school).id
            if TargetPopulation.objects.filter(population=school).exists()
            else -1
        )
        year = (
            request.user.profile.expected_graduation.year
            if request.user.profile.expected_graduation
            else None
        )
        year_id = (
            TargetPopulation.objects.get(population=year).id
            if TargetPopulation.objects.filter(population=year).exists()
            else -1
        )

        # return list of valid votes that user was targeted for
        # but has yet to answer
        return Response(
            RetrievePollSerializer(
                Poll.objects.filter(
                    ~Q(
                        id__in=PollVote.objects.filter(user=self.request.user).values_list(
                            "poll_id"
                        )
                    ),
                    Q(target_populations__in=[school_id, year_id]),
                    expire_date__gte=timezone.localtime(),
                    approved=True,
                ),
                many=True,
            ).data
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def review(self, request):
        # returns list of unapproved polls where admin hasn't left comment
        return Response(
            RetrievePollSerializer(
                Poll.objects.filter(approved=False, admin_comment=None), many=True
            ).data
        )


# TODO: fix this!
# TODO: add admin analytics in addition to user history
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
        return (
            PollOption.objects.all()
            if self.request.user.is_superuser
            else PollOption.objects.filter(poll__in=Poll.objects.filter(user=self.request.user))
        )


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
        # only user can see, create, update, and/or destroy their own votes
        return PollVote.objects.filter(user=self.request.user)
