from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import Trunc
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser

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


User = get_user_model()


class UserInfo(APIView):
    """Returns User information"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": get_user_info(request.user)})


class UserClubs(APIView):
    """Returns list of clubs a User can post on the behalf of"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        club_data = []
        for club in get_user_clubs(request.user):
            club_data.append(get_club_info(request.user, club["club"]["code"]))
        return Response({"clubs": club_data})


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
        # all polls if superuser, polls corresponding to club for regular user
        return (
            Poll.objects.all()
            if self.request.user.is_superuser
            else Poll.objects.filter(
                club_code__in=[x["club"]["code"] for x in get_user_clubs(self.request.user)]
            )
        )

    @action(detail=False, methods=["post"])
    def browse(self, request):
        """Returns list of all possible polls user can answer but has yet to
        For admins, returns list of all polls they have not voted for and have yet to expire
        """

        id_hash = request.data["id_hash"]

        # unvoted polls in draft/approaved mode for superuser
        # unvoted and approved polls within time frame for regular user
        unfiltered_polls = (
            Poll.objects.filter(
                ~Q(id__in=PollVote.objects.filter(id_hash=id_hash).values_list("poll_id")),
                Q(status=Poll.STATUS_DRAFT) | Q(status=Poll.STATUS_APPROVED),
                expire_date__gte=timezone.localtime(),
            )
            if request.user.is_superuser
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
        if not request.user.is_superuser:
            for unfiltered_poll in unfiltered_polls:
                if not check_targets(unfiltered_poll, request.user):
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
            RetrievePollSerializer(polls.distinct().order_by("expire_date"), many=True).data
        )

    @action(detail=False, methods=["get"], permission_classes=[IsSuperUser])
    def review(self, request):
        """Returns list of all Polls that admins still need to approve of"""
        return Response(
            RetrievePollSerializer(Poll.objects.filter(status=Poll.STATUS_DRAFT), many=True,).data
        )

    @action(detail=True, methods=["get"])
    def option_view(self, request, pk=None):
        """Returns information on specific poll, including options and vote counts"""
        return Response(RetrievePollSerializer(Poll.objects.filter(id=pk).first(), many=False).data)


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
            else PollOption.objects.filter(
                poll__in=Poll.objects.filter(
                    club_code__in=[x["club"]["code"] for x in get_user_clubs(self.request.user)]
                )
            )
        )


class PollVotes(viewsets.ModelViewSet):
    """
    create:
    Create a Poll Vote.
    """

    permission_classes = [PollOwnerPermission | IsSuperUser]
    serializer_class = PollVoteSerializer

    def get_queryset(self):
        return PollVote.objects.none()

    @action(detail=False, methods=["post"])
    def recent(self, request):

        id_hash = request.data["id_hash"]

        poll_votes = PollVote.objects.filter(id_hash=id_hash).order_by("-created_date").first()
        return Response(RetrievePollVoteSerializer(poll_votes).data)

    @action(detail=False, methods=["post"])
    def all(self, request):

        id_hash = request.data["id_hash"]

        poll_votes = PollVote.objects.filter(id_hash=id_hash).order_by("-created_date")
        return Response(RetrievePollVoteSerializer(poll_votes, many=True).data)


class PollVoteStatistics(APIView):
    """Returns time series of all votes for a particular poll"""

    permission_classes = [TimeSeriesPermission | IsSuperUser]

    def get(self, request, poll_id):
        return Response(
            {
                "time_series": PollVote.objects.filter(poll__id=poll_id)
                .annotate(date=Trunc("created_date", "day"))
                .values("date")
                .annotate(votes=Count("date"))
                .order_by("date"),
                "poll_statistics": get_demographic_breakdown(poll_id),
            }
        )


class Posts(viewsets.ModelViewSet):
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
    parser_classes = (MultiPartParser, JSONParser)

    def get_queryset(self):
        return (
            Post.objects.all()
            if self.request.user.is_superuser
            else Post.objects.filter(
                club_code__in=[x["club"]["code"] for x in get_user_clubs(self.request.user)]
            )
        )

    def create(self, request, *args, **kwargs):
        print(self.request.FILES)
        content_disposition = request.META.get('HTTP_CONTENT_DISPOSITION', None)
        print(content_disposition)

        return super().create(request, args, kwargs)

    @action(detail=False, methods=["get"])
    def browse(self, request):
        """
        Returns a list of all posts that are targeted at the current user
        For admins, returns list of posts that they have not approved and have yet to expire
        """
        unfiltered_posts = (
            Post.objects.filter(
                Q(status=Post.STATUS_DRAFT) | Q(status=Post.STATUS_APPROVED),
                expire_date__gte=timezone.localtime(),
            )
            if request.user.is_superuser
            else Post.objects.filter(
                status=Post.STATUS_APPROVED,
                start_date__lte=timezone.localtime(),
                expire_date__gte=timezone.localtime(),
            )
        )

        # list of polls where user doesn't identify with
        # target populations
        bad_posts = []

        # commented out to make posts
        # if not request.user.is_superuser:
        #     for unfiltered_post in unfiltered_posts:
        #         if not check_targets(unfiltered_post, request.user):
        #             bad_posts.append(unfiltered_post.id)

        # excludes the bad polls
        posts = unfiltered_posts.exclude(id__in=bad_posts)

        return Response(PostSerializer(posts.distinct().order_by("expire_date"), many=True).data)

    @action(detail=False, methods=["get"], permission_classes=[IsSuperUser])
    def review(self, request):
        """Returns a list of all Posts that admins still need to approve of"""
        return Response(
            PostSerializer(Post.objects.filter(status=Poll.STATUS_DRAFT), many=True,).data
        )
