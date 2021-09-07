from django.db.models import Count, Q
from django.db.models.functions import Trunc
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from portal.logic import get_demographic_breakdown, get_user_populations
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
    """List view to see which populations a poll can select"""

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
        """Returns list of all possible polls user can answer but has yet to"""
        return Response(
            RetrievePollSerializer(
                Poll.objects.filter(
                    ~Q(
                        id__in=PollVote.objects.filter(user=self.request.user).values_list(
                            "poll_id"
                        )
                    ),
                    Q(target_populations__in=get_user_populations(request.user)),
                    expire_date__gte=timezone.localtime(),
                    approved=True,
                ),
                many=True,
            ).data
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def review(self, request):
        """Returns list of all Polls that admins still need to approve of"""
        return Response(
            RetrievePollSerializer(
                Poll.objects.filter(approved=False, admin_comment=None), many=True
            ).data
        )


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
            context = {
                "id": None,
                "poll": entry,
                "poll_options": PollOptionSerializer(
                    PollOption.objects.filter(poll__id=entry["id"]), many=True
                ).data,
            }
            history_list.append(context)
        for entry in history_list:
            entry["poll_statistics"] = get_demographic_breakdown(entry["poll"]["id"])
        return Response(sorted(history_list, key=lambda i: i["poll"]["expire_date"], reverse=True))


class PollVoteTimeSeries(APIView):
    """Returns time series of all votes for a particular poll"""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        return Response(
            {
                "time_series": PollVote.objects.filter(poll__id=id)
                .annotate(date=Trunc("created_date", "day"))
                .values("date")
                .annotate(votes=Count("date"))
                .order_by("date")
            }
        )


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
