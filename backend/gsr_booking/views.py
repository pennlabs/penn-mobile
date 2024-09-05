from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from gsr_booking.api_wrapper import APIError, GSRBooker, WhartonGSRBooker
from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking
from gsr_booking.serializers import (
    GroupMembershipSerializer,
    GroupSerializer,
    GSRSerializer,
    UserSerializer,
)
from pennmobile.analytics import Metric, record_analytics


User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Can specify `me` instead of the `username` to retrieve details on the current user.
    """

    queryset = User.objects.all().prefetch_related(
        Prefetch("booking_groups", Group.objects.filter(memberships__accepted=True))
    )
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    lookup_field = "username"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["username", "first_name", "last_name"]

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        param = self.kwargs[lookup_url_kwarg]
        if param == "me":
            return self.request.user
        else:
            return super().get_object()

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.none()

        queryset = User.objects.all()
        queryset = queryset.prefetch_related(
            Prefetch(
                "memberships",
                GroupMembership.objects.filter(
                    group__in=self.request.user.booking_groups.all(), accepted=True
                ),
            )
        )
        return queryset

    @action(detail=True, methods=["get"])
    def invites(self, request, username=None):
        """
        Retrieve all invites for a given user.
        """

        user = get_object_or_404(User, username=username)
        return Response(
            GroupMembershipSerializer(
                GroupMembership.objects.filter(
                    user=user, accepted=False, group__in=self.request.user.booking_groups.all()
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
            return Response({"message": "cannot decline an invite that has been accepted."}, 400)

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

            date_format = "%Y-%m-%dT%H:%M:%S%z"
            start_date_obj = datetime.strptime(start, date_format)
            end_date_obj = datetime.strptime(end, date_format)

            gsr_analytic = (
                "gsr.book.",
                str(room_id).replace(" ", "").upper() + ".",
                str(room_name).replace(" ", "").upper(),
            )

            elapsed_minutes = (end_date_obj - start_date_obj).total_seconds() / 60
            record_analytics(gsr_analytic + ".start", request.user.username, start)
            record_analytics(
                gsr_analytic + ".duration", request.user.username, str(elapsed_minutes)
            )

            return Response({"detail": "success"})
        except APIError as e:
            return Response({"error": str(e)}, status=400)


class CancelRoom(APIView):
    """
    Cancels  a room for a given user
    """

    permission_classes = [IsAuthenticated]

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
