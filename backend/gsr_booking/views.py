from typing import Optional

from django.db.models import Manager, Prefetch, Q, QuerySet
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from gsr_booking.api_wrapper import GSRBooker, WhartonGSRBooker
from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking
from gsr_booking.serializers import GroupMembershipSerializer, GroupSerializer, GSRSerializer
from pennmobile.analytics import Metric, record_analytics
from utils.errors import APIError
from utils.types import get_user


class MyMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupMembershipSerializer

    def get_queryset(self) -> QuerySet[GroupMembership, Manager[GroupMembership]]:
        return GroupMembership.objects.filter(user=self.request.user, accepted=True)

    @action(detail=False, methods=["get"])
    def invites(self, request: Request) -> Response:
        """
        Retrieve all invites for a given user.
        """

        request_user = get_user(self.request)
        return Response(
            GroupMembershipSerializer(
                GroupMembership.objects.filter(
                    user=get_user(request),
                    accepted=False,
                    group__in=request_user.booking_groups.all(),
                ),
                many=True,
            ).data
        )


class GroupMembershipViewSet(viewsets.ModelViewSet[GroupMembership]):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "group"]
    permission_classes = [IsAuthenticated]
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer

    def get_queryset(self) -> QuerySet[GroupMembership, Manager[GroupMembership]]:
        user = get_user(self.request)
        if not user.is_authenticated:
            return GroupMembership.objects.none()

        return GroupMembership.objects.filter(
            Q(id__in=user.memberships.all())
            | Q(
                group__in=Group.objects.filter(
                    memberships__in=GroupMembership.objects.filter(user=user, type="A")
                )
            )
        )

    @action(detail=False, methods=["post"])
    def invite(self, request: Request) -> Response | HttpResponseForbidden:
        """
        Invite a user to a group.
        """
        group_id = request.data.get("group")
        group = get_object_or_404(Group, pk=group_id)

        # don't invite when user already in group
        if group.has_member(get_user(request)):
            return HttpResponseForbidden()

        return Response({"message": "invite(s) sent."})

    @action(detail=True, methods=["post"])
    def accept(
        self, request: Request, pk: Optional[int] = None
    ) -> Response | HttpResponseForbidden:
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        user = get_user(request)
        if membership.user is None or membership.user != user:
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
    def decline(
        self, request: Request, pk: Optional[int] = None
    ) -> Response | HttpResponseForbidden:
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        if membership.user is None or membership.user != get_user(request):
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


class GroupViewSet(viewsets.ModelViewSet[Group]):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Group, Manager[Group]]:
        user = get_user(self.request)
        if not user.is_authenticated:
            return Group.objects.none()
        return (
            super()
            .get_queryset()
            .filter(members=user)
            .prefetch_related(
                Prefetch("memberships", GroupMembership.objects.filter(accepted=True))
            )
        )


class Locations(generics.ListAPIView[GSR]):
    """Lists all available locations to book from"""

    serializer_class = GSRSerializer
    queryset = GSR.objects.all()


class RecentGSRs(generics.ListAPIView[GSR]):
    """Lists 2 most recent GSR rooms for Home page"""

    serializer_class = GSRSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[GSR, Manager[GSR]]:
        return GSR.objects.filter(
            id__in=GSRBooking.objects.filter(user=get_user(self.request), is_cancelled=False)
            .distinct()
            .order_by("-end")[:2]
            .values_list("gsr", flat=True)
        )


class CheckWharton(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = get_user(request)
        return Response(
            {
                "is_wharton": user.booking_groups.filter(name="Penn Labs").exists()
                or WhartonGSRBooker.is_wharton(user)
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

    def get(self, request: Request, lid: int, gid: str) -> Response:

        start = request.GET.get("start", None)
        end = request.GET.get("end", None)

        try:
            user = get_user(request)
            return Response(
                GSRBooker.get_availability(
                    lid,
                    gid,
                    start,
                    end,
                    user,
                    user.booking_groups.filter(name="Penn Labs").first(),
                )
            )
        except APIError as e:
            return Response({"error": str(e)}, status=400)


class BookRoom(APIView):
    """Books room in any GSR in the availability route"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        start = request.data["start_time"]
        end = request.data["end_time"]
        gid = request.data["gid"]
        room_id = request.data["id"]
        room_name = request.data["room_name"]
        user = get_user(request)

        try:
            GSRBooker.book_room(
                gid,
                room_id,
                room_name,
                start,
                end,
                user,
                user.booking_groups.filter(name="Penn Labs").first(),
            )

            record_analytics(Metric.GSR_BOOK, user.username)

            return Response({"detail": "success"})
        except APIError as e:
            return Response({"error": str(e)}, status=400)


class CancelRoom(APIView):
    """
    Cancels  a room for a given user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        booking_id = request.data["booking_id"]
        user = get_user(request)
        try:
            GSRBooker.cancel_room(booking_id, user)
            return Response({"detail": "success"})
        except APIError as e:
            return Response({"error": str(e)}, status=400)


class ReservationsView(APIView):
    """
    Gets reservations for a User
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = get_user(request)
        return Response(
            GSRBooker.get_reservations(user, user.booking_groups.filter(name="Penn Labs").first())
        )
