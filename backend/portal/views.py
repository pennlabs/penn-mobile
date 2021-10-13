from django.db.models import Count, Q
from django.db.models.functions import Trunc
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from portal.logic import get_demographic_breakdown
from portal.models import Poll, PollOption, PollVote, TargetPopulation
from portal.permissions import (
    IsSuperUser,
    OptionOwnerPermission,
    PollOwnerPermission,
    PostOwnerPermission,
    TimeSeriesPermission,
)
from portal.serializers import (
    PollOptionSerializer,
    PollSerializer,
    PollVoteSerializer,
    PostSerializer,
    RetrievePollSerializer,
    RetrievePollVoteSerializer,
    TargetPopulationSerializer,
)


class TargetPopulations(generics.ListAPIView):
    """List view to see which populations a poll can select"""

    permission_classes = [IsAuthenticated]
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

    permission_classes = [PollOwnerPermission | IsSuperUser]
    serializer_class = PollSerializer

    def get_queryset(self):
        return (
            Poll.objects.all()
            if self.request.user.is_superuser
            else Poll.objects.filter(user=self.request.user)
        )

    @action(detail=False, methods=["get"])
    def browse(self, request):
        """Returns list of all possible polls user can answer but has yet to
        For admins, returns list of all polls they have not voted for and have yet to expire
        """

        polls = (
            Poll.objects.filter(
                ~Q(id__in=PollVote.objects.filter(user=self.request.user).values_list("poll_id")),
                Q(approved=True) | Q(admin_comment=None),
                expire_date__gte=timezone.localtime(),
            )
            if request.user.is_superuser
            else Poll.objects.filter(
                ~Q(id__in=PollVote.objects.filter(user=self.request.user).values_list("poll_id")),
                # Q(target_populations__in=get_user_populations(request.user)),
                start_date__lte=timezone.localtime(),
                expire_date__gte=timezone.localtime(),
                approved=True,
            )
        )

        return Response(
            RetrievePollSerializer(
                polls.distinct().order_by("approved", "start_date"), many=True,
            ).data
        )

    @action(detail=False, methods=["get"], permission_classes=[IsSuperUser])
    def review(self, request):
        """Returns list of all Polls that admins still need to approve of"""
        return Response(
            RetrievePollSerializer(
                Poll.objects.filter(Q(admin_comment=None) | Q(admin_comment=""), approved=False),
                many=True,
            ).data
        )


class RetrievePollVotes(viewsets.ModelViewSet):
    """Retrieve history of polls and their statistics"""

    permission_classes = [IsAuthenticated | IsSuperUser]
    serializer_class = RetrievePollSerializer

    def get_queryset(self):
        return (
            Poll.objects.all()
            if self.request.user.is_superuser
            else Poll.objects.filter(user=self.request.user)
        )

    def list(self, request):

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
        return Response(sorted(history_list, key=lambda i: i["poll"]["expire_date"], reverse=True))

    @action(detail=False, methods=["get"])
    def recent(self, request, pk=None):
        user_poll_votes = (
            PollVote.objects.filter(user=request.user).order_by("-created_date").first()
        )
        return Response(RetrievePollVoteSerializer(user_poll_votes).data)


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

    permission_classes = [OptionOwnerPermission | IsSuperUser]
    serializer_class = PollOptionSerializer

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

    permission_classes = [PollOwnerPermission | IsSuperUser]
    serializer_class = PollVoteSerializer

    def get_queryset(self):
        # only user can see, create, update, and/or destroy their own votes
        return PollVote.objects.filter(user=self.request.user)


class PollVoteStatistics(APIView):
    """Returns time series of all votes for a particular poll"""

    permission_classes = [TimeSeriesPermission | IsSuperUser]

    def get(self, request, id):
        return Response(
            {
                "time_series": PollVote.objects.filter(poll__id=id)
                .annotate(date=Trunc("created_date", "day"))
                .values("date")
                .annotate(votes=Count("date"))
                .order_by("date"),
                "poll_statistics": get_demographic_breakdown(id),
            }
        )


class Post(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [PostOwnerPermission | IsSuperUser]

    def get_queryset(self):
        return (
            Post.objects.all()
            if self.request.user.is_superuser
            else Poll.objects.filter(user=self.request.user)
        )
