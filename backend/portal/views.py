from typing import Any, List, Optional

from django.db.models import Count, Q
from django.db.models.functions import Trunc
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from pennmobile.analytics import Metric, record_analytics
from portal.logic import (
    check_targets,
    get_club_info,
    get_demographic_breakdown,
    get_user_clubs,
    get_user_info,
)
from portal.models import Poll, PollOption, PollVote, Post, TargetPopulation
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
from portal.types import (
    PollOptionQuerySet,
    PollQuerySet,
    PollVoteQuerySet,
    PostQuerySet,
    VoteStatistics,
)
from utils.types import AuthRequest, get_auth_user


class UserInfo(APIView):
    """Returns User information"""

    permission_classes = [IsAuthenticated]

    def get(self, request: AuthRequest) -> Response:
        return Response({"user": get_user_info(request.user)})


class UserClubs(APIView):
    """Returns list of clubs a User can post on the behalf of"""

    permission_classes = [IsAuthenticated]

    def get(self, request: AuthRequest) -> Response:
        club_data = [
            get_club_info(request.user, club["club"]["code"])
            for club in get_user_clubs(request.user)
        ]
        return Response({"clubs": club_data})


class TargetPopulations(generics.ListAPIView[TargetPopulation]):
    """List view to see which populations a poll can select"""

    permission_classes = [IsAuthenticated]
    serializer_class = TargetPopulationSerializer
    queryset = TargetPopulation.objects.all()


class Polls(viewsets.ModelViewSet[Poll]):
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

    def get_queryset(self) -> PollQuerySet:
        # all polls if superuser, polls corresponding to club for regular user
        user = get_auth_user(self.request)
        return (
            Poll.objects.all()
            if user.is_superuser
            else Poll.objects.filter(
                club_code__in=[x["club"]["code"] for x in get_user_clubs(user)]
            )
        )

    @action(detail=False, methods=["post"])
    def browse(self, request: AuthRequest) -> Response:
        """Returns list of all possible polls user can answer but has yet to
        For admins, returns list of all polls they have not voted for and have yet to expire
        """

        id_hash = request.data["id_hash"]
        user = get_auth_user(request)

        # unvoted polls in draft/approaved mode for superuser
        # unvoted and approved polls within time frame for regular user
        unfiltered_polls = (
            Poll.objects.filter(
                ~Q(id__in=PollVote.objects.filter(id_hash=id_hash).values_list("poll_id")),
                Q(status=Poll.STATUS_DRAFT) | Q(status=Poll.STATUS_APPROVED),
                expire_date__gte=timezone.localtime(),
            )
            if user.is_superuser
            else Poll.objects.filter(
                ~Q(id__in=PollVote.objects.filter(id_hash=id_hash).values_list("poll_id")),
                status=Poll.STATUS_APPROVED,
                start_date__lte=timezone.localtime(),
                expire_date__gte=timezone.localtime(),
            )
        )

        # list of polls where user doesn't identify with
        # target populations
        bad_polls = []
        if not user.is_superuser:
            for unfiltered_poll in unfiltered_polls:
                if not check_targets(unfiltered_poll, user):
                    bad_polls.append(unfiltered_poll.id)

        # excludes the bad polls
        polls = unfiltered_polls.exclude(id__in=bad_polls)

        # # TODO: fix sorting DRAFT before APPROVED if the functionality is necessary
        # # sort draft first, then approved
        # CASE_SQL = '(case when status="DRAFT" then 1 when status="APPROVED" then 2 end)'

        # return Response(
        #     RetrievePollSerializer(
        #         polls.distinct().extra(
        #             select={"status_order": CASE_SQL}, order_by=["status_order", "expire_date"]
        #         ),
        #         many=True,
        #     ).data
        # )

        return Response(
            RetrievePollSerializer(
                polls.distinct().order_by("-priority", "start_date", "expire_date"), many=True
            ).data
        )

    @action(detail=False, methods=["get"], permission_classes=[IsSuperUser])
    def review(self, request: Request) -> Response:
        """Returns list of all Polls that admins still need to approve of"""
        return Response(
            RetrievePollSerializer(Poll.objects.filter(status=Poll.STATUS_DRAFT), many=True).data
        )

    @action(detail=True, methods=["get"])
    def option_view(self, request: Request, pk: Optional[int] = None) -> Response:
        """Returns information on specific poll, including options and vote counts"""
        return Response(RetrievePollSerializer(Poll.objects.filter(id=pk).first(), many=False).data)


class PollOptions(viewsets.ModelViewSet[PollOption]):
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

    def get_queryset(self) -> PollOptionQuerySet:
        # if user is admin, they can update anything
        # if user is not admin, they can only update their own options
        user = get_auth_user(self.request)
        return (
            PollOption.objects.all()
            if user.is_superuser
            else PollOption.objects.filter(
                poll__in=Poll.objects.filter(
                    club_code__in=[x["club"]["code"] for x in get_user_clubs(user)]
                )
            )
        )


class PollVotes(viewsets.ModelViewSet[PollVote]):
    """
    create:
    Create a Poll Vote.
    """

    permission_classes = [PollOwnerPermission | IsSuperUser]
    serializer_class = PollVoteSerializer

    def get_queryset(self) -> PollVoteQuerySet:
        return PollVote.objects.none()

    @action(detail=False, methods=["post"])
    def recent(self, request: Request) -> Response:

        id_hash = request.data["id_hash"]

        poll_votes = PollVote.objects.filter(id_hash=id_hash).order_by("-created_date").first()
        return Response(RetrievePollVoteSerializer(poll_votes).data)

    @action(detail=False, methods=["post"])
    def all(self, request: Request) -> Response:

        id_hash = request.data["id_hash"]

        poll_votes = PollVote.objects.filter(id_hash=id_hash).order_by("-created_date")
        return Response(RetrievePollVoteSerializer(poll_votes, many=True).data)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = get_auth_user(request)
        record_analytics(Metric.PORTAL_POLL_VOTED, user.username)
        return super().create(request, *args, **kwargs)


class PollVoteStatistics(APIView):
    """Returns time series of all votes for a particular poll"""

    permission_classes = [TimeSeriesPermission | IsSuperUser]

    def get(self, request: Request, poll_id: int) -> Response:
        time_series = (
            PollVote.objects.filter(poll__id=poll_id)
            .annotate(date=Trunc("created_date", "day"))
            .values("date")
            .annotate(votes=Count("date"))
            .order_by("date")
        )

        statistics: VoteStatistics = {
            "time_series": time_series,
            "poll_statistics": get_demographic_breakdown(poll_id),
        }
        return Response(statistics)


class Posts(viewsets.ModelViewSet[Post]):
    """
    browse:
    returns a list of Posts that are targeted at the current user.
    Admins sees all the posts(?)

    create:
    Create a Post

    partial_update:
    Update certain fields in the Post.
    Need to be the admin or the creator.

    destroy:
    Delete a Post.
    Need to be the admin or the creator.
    """

    permission_classes = [PostOwnerPermission | IsSuperUser]
    serializer_class = PostSerializer

    def get_queryset(self) -> PostQuerySet:
        user = get_auth_user(self.request)
        return (
            Post.objects.all()
            if user.is_superuser
            else Post.objects.filter(
                club_code__in=[x["club"]["code"] for x in get_user_clubs(user)]
            )
        )

    @action(detail=False, methods=["get"])
    def browse(self, request: AuthRequest) -> Response:
        """
        Returns a list of all posts that are targeted at the current user
        For admins, returns list of posts that they have not approved and have yet to expire
        """
        user = get_auth_user(request)
        unfiltered_posts = (
            Post.objects.filter(
                Q(status=Post.STATUS_DRAFT) | Q(status=Post.STATUS_APPROVED),
                expire_date__gte=timezone.localtime(),
            )
            if user.is_superuser
            else Post.objects.filter(
                status=Post.STATUS_APPROVED,
                start_date__lte=timezone.localtime(),
                expire_date__gte=timezone.localtime(),
            )
        )

        # list of polls where user doesn't identify with
        # target populations
        bad_posts: List[int] = []

        # commented out to make posts
        # if not request.user.is_superuser:
        #     for unfiltered_post in unfiltered_posts:
        #         if not check_targets(unfiltered_post, request.user):
        #             bad_posts.append(unfiltered_post.id)

        # excludes the bad polls
        posts = unfiltered_posts.exclude(id__in=bad_posts)

        return Response(
            PostSerializer(
                posts.distinct().order_by("-priority", "start_date", "expire_date"), many=True
            ).data
        )

    @action(detail=False, methods=["get"], permission_classes=[IsSuperUser])
    def review(self, request: Request) -> Response:
        """Returns a list of all Posts that admins still need to approve of"""
        return Response(
            PostSerializer(Post.objects.filter(status=Poll.STATUS_DRAFT), many=True).data
        )
