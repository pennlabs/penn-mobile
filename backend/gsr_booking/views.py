from analytics.entries import FuncEntry, ViewEntry
from dateutil.parser import parse as parse_datetime
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from gsr_booking.api_wrapper import APIError, GSRBooker, WhartonGSRBooker, PennGroupsGSRBooker
from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, GSRShareCode
from gsr_booking.permissions import IsShareCodeOwner
from gsr_booking.serializers import (
    GroupMembershipSerializer,
    GroupSerializer,
    GSRSerializer,
    GSRShareCodeSerializer,
    SharedGSRBookingSerializer,
)
from pennmobile.analytics import LabsAnalytics
from utils.cache import Cache

User = get_user_model()


class MyMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupMembershipSerializer

    def get_queryset(self):
        return GroupMembership.objects.filter(user=self.request.user, accepted=True)

    @action(detail=False, methods=["get"])
    def invites(self, request):
        """
        Retrieve all invites for a given user.
        """
        return Response(
            GroupMembershipSerializer(
                GroupMembership.objects.filter(
                    user=request.user,
                    accepted=False,
                    group__in=self.request.user.booking_groups.all(),
                ),
                many=True,
            ).data
        )


class GroupMembershipViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "group"]
    permission_classes = [IsAuthenticated]
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated or not hasattr(self.request.user, "memberships"):
            return GroupMembership.objects.none()
        return GroupMembership.objects.filter(
            Q(id__in=self.request.user.memberships.all())
            | Q(
                group__in=Group.objects.filter(
                    memberships__in=GroupMembership.objects.filter(user=self.request.user, type="A")
                )
            )
        )

    @action(detail=False, methods=["post"])
    def invite(self, request):
        """
        Invite a user to a group.
        """
        group_id = request.data.get("group")
        group = get_object_or_404(Group, pk=group_id)

        # don't invite when user already in group
        if group.has_member(request.user):
            return HttpResponseForbidden()

        return Response({"message": "invite(s) sent."})

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        if membership.user is None or membership.user != request.user:
            return HttpResponseForbidden()

        if not membership.is_invite:
            return Response({"message": "invite has already been accepted"}, 400)

        membership.accepted = True
        membership.save()
        return Response(
            {
                "message": "group joined",
                "user": membership.user.username,
                "group": membership.group_id,
            }
        )

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        if membership.user is None or membership.user != request.user:
            return HttpResponseForbidden()
        if not membership.is_invite:
            return Response(
                {"message": "cannot decline an invite that has been accepted."}, status=400
            )

        resp = {
            "message": "invite declined",
            "user": membership.user.username,
            "group": membership.group_id,
        }
        membership.delete()
        return Response(resp)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Group.objects.none()
        return (
            super()
            .get_queryset()
            .filter(members=self.request.user)
            .prefetch_related(
                Prefetch("memberships", GroupMembership.objects.filter(accepted=True))
            )
        )


class Locations(generics.ListAPIView):
    """Lists all available locations to book from"""

    serializer_class = GSRSerializer
    permission_classes = [IsAuthenticated]

    def get_permission_level(self, user):
        """
        Determine the user's permission level for caching purposes.
        Returns a tuple of booleans: (is_penn_labs, is_wharton, is_seas)
        """
        is_penn_labs = user.booking_groups.filter(name="Penn Labs").exists()

        if is_penn_labs:
            # Penn Labs users see everything, so we can cache at that level
            return "penn_labs"

        # Check Wharton and SEAS access
        is_wharton = False
        is_seas = False

        try:
            is_wharton = WhartonGSRBooker.is_wharton(user)
        except APIError:
            pass

        try:
            is_seas = PennGroupsGSRBooker.is_seas(user)
        except APIError:
            pass

        # Create a permission key based on access levels
        return f"wharton_{is_wharton}_seas_{is_seas}"

    def list(self, request, *args, **kwargs):
        """
        Override list to implement per-permission-level caching
        """
        permission_level = self.get_permission_level(request.user)
        cache_key = f"gsr_locations:{permission_level}"

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # If not in cache, get the data
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        # Cache the response for a week (locations don't change often)
        cache.set(cache_key, serializer.data, Cache.DAY * 7)

        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user

        # Penn Labs members can see all GSRs
        if user.booking_groups.filter(name="Penn Labs").exists():
            return GSR.objects.all()

        # For other users, filter based on their memberships
        accessible_kinds = []

        # Check if user has Wharton access
        try:
            if WhartonGSRBooker.is_wharton(user):
                accessible_kinds.append(GSR.KIND_WHARTON)
        except APIError:
            # If API call fails, user doesn't have Wharton access
            pass

        # Check if user has SEAS access
        try:
            if PennGroupsGSRBooker.is_seas(user):
                accessible_kinds.append(GSR.KIND_PENNGROUPS)
        except APIError:
            # If API call fails, user doesn't have SEAS access
            pass

        # LibCal is accessible to everyone
        accessible_kinds.append(GSR.KIND_LIBCAL)

        return GSR.objects.filter(kind__in=accessible_kinds)


class RecentGSRs(generics.ListAPIView):
    """Lists 2 most recent GSR rooms for Home page"""

    serializer_class = GSRSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GSR.objects.filter(
            id__in=GSRBooking.objects.filter(user=self.request.user, is_cancelled=False)
            .distinct()
            .order_by("-end")[:2]
            .values_list("gsr", flat=True)
        )


class CheckWharton(APIView):
    """Check if user has Wharton privilege"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "is_wharton": request.user.booking_groups.filter(name="Penn Labs").exists()
                or WhartonGSRBooker.is_wharton(request.user)
            }
        )


class CheckSEAS(APIView):
    """Check if user has SEAS status"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "is_seas": request.user.booking_groups.filter(name="Penn Labs").exists()
                or PennGroupsGSRBooker.is_seas(request.user)
            }
        )


class Availability(APIView):
    """
    Returns JSON containing all rooms for a given building.
    Usage:
        /studyspaces/availability/<building> gives all rooms for the next 24 hours
        /studyspaces/availability/<building>?start=2018-25-01 gives all rooms in the start date
        /studyspaces/availability/<building>?start=...&end=... gives all rooms between the two days
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, lid, gid):

        start = request.GET.get("start")
        end = request.GET.get("end")

        try:
            return Response(
                GSRBooker.get_availability(
                    lid,
                    gid,
                    start,
                    end,
                    request.user,
                    request.user.booking_groups.filter(name="Penn Labs").first(),
                )
            )
        except APIError as e:
            return Response({"error": str(e)}, status=400)


# Records analytics for GSR start time, room id, and duration
@LabsAnalytics.record_apiview(
    ViewEntry(name="booking_start_time", get_value=lambda req, res: req.data.get("start_time")),
    ViewEntry(name="booking_room_id", get_value=lambda req, res: req.data.get("id")),
    ViewEntry(
        name="gsr_booking_duration",
        get_value=lambda req, res: (
            (
                parse_datetime(req.data.get("end_time"))
                - parse_datetime(req.data.get("start_time"))
            ).total_seconds()
            / 60
        ),
    ),
)
class BookRoom(APIView):
    """Books room in any GSR in the availability route"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        start = request.data["start_time"]
        end = request.data["end_time"]
        gid = request.data["gid"]
        room_id = request.data["id"]
        room_name = request.data["room_name"]

        try:
            GSRBooker.book_room(
                gid,
                room_id,
                room_name,
                start,
                end,
                request.user,
                request.user.booking_groups.filter(name="Penn Labs").first(),
            )
            return Response({"detail": "success"})
        except APIError as e:
            return Response({"error": str(e)}, status=400)


class CancelRoom(APIView):
    """
    Cancels  a room for a given user
    """

    permission_classes = [IsAuthenticated]

    @LabsAnalytics.record_api_function(
        FuncEntry(
            name="gsr_cancellation_booking_id",
            get_value_with_args=lambda _self, request: request.data.get("booking_id"),
        )
    )
    def post(self, request):
        booking_id = request.data["booking_id"]

        try:
            GSRBooker.cancel_room(booking_id, request.user)
            return Response({"detail": "success"})
        except APIError as e:
            return Response({"error": str(e)}, status=400)


class ReservationsView(APIView):
    """
    Gets reservations for a User
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            GSRBooker.get_reservations(
                request.user, request.user.booking_groups.filter(name="Penn Labs").first()
            )
        )


class GSRShareCodeViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for creating, retrieving, and deleting GSR share codes.
    """

    lookup_field = "code"
    lookup_value_regex = r"[A-Za-z0-9_-]{8}"
    permission_classes = [IsShareCodeOwner]
    queryset = GSRShareCode.objects.all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SharedGSRBookingSerializer
        return GSRShareCodeSerializer

    def retrieve(self, request, *args, **kwargs):
        share_code = self.get_object()

        if not share_code.is_valid():
            return Response(
                {"error": "This share code has expired or been revoked by owner"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(share_code.booking)
        return Response(serializer.data)

    # create() is inherited from CreateModelMixin
    # destroy() is inherited from DestroyModelMixin
