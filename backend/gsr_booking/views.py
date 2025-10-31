from analytics.entries import FuncEntry, ViewEntry
from dateutil.parser import parse as parse_datetime
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from gsr_booking.api_wrapper import APIError, GSRBooker, WhartonGSRBooker
from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, GSRShareCode
from gsr_booking.serializers import (
    GroupMembershipSerializer,
    GroupSerializer,
    GSRSerializer,
    GSRShareCodeSerializer,
    SharedGSRBookingSerializer,
)
from pennmobile.analytics import LabsAnalytics


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
    queryset = GSR.objects.all()


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

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "is_wharton": request.user.booking_groups.filter(name="Penn Labs").exists()
                or WhartonGSRBooker.is_wharton(request.user)
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


class CreateShareCode(APIView):
    """
    Creates or retrieves a share code for a GSR booking
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = request.data.get("booking_id")

        if not booking_id:
            return Response({"error": "booking_id is required"}, status=400)

        booking = GSRBooking.objects.filter(id=booking_id).first()
        if booking is None:
            return Response({"error": "Booking not found"}, status=404)

        owner = booking.reservation.creator if booking.reservation else booking.user
        if owner != request.user and not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to share this booking"},
                status=403,
            )

        try:
            existing_code = GSRShareCode.objects.filter(booking=booking).first()

            if existing_code and existing_code.is_valid():
                serializer = GSRShareCodeSerializer(existing_code)
                return Response(serializer.data)

            share_code = GSRShareCode.objects.create(
                code=GSRShareCode.generate_code(),
                booking=booking,
                owner=request.user,
            )

            serializer = GSRShareCodeSerializer(share_code)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except APIError as e:
            return Response({"error": str(e)}, status=400)


class ViewSharedBooking(APIView):
    """
    View a booking using a share code, no authentication is needed
    """

    permission_classes = [AllowAny]

    def get(self, request, code):
        try:
            share_code = GSRShareCode.objects.filter(code=code).first()

            if share_code is None:
                return Response({"error": "Invalid share code"}, status=404)

            if not share_code.is_valid():
                return Response(
                    {"error": "This share code has expired or been revoked"},
                    status=400,
                )

            serializer = SharedGSRBookingSerializer(share_code.booking)
            return Response(serializer.data)
        except APIError as e:
            return Response({"error": str(e)}, status=400)


class RevokeShareCode(APIView):
    """
    Revoke a share code (only owner can revoke)
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, code):
        share_code = GSRShareCode.objects.filter(code=code).first()

        if share_code is None:
            return Response({"error": "Invalid share code"}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is the owner or staff
        if share_code.owner != request.user and not request.user.is_staff:
            return Response({"error": "You can only revoke your own share codes"}, status=403)

        share_code.delete()

        return Response({"detail": "success"})
