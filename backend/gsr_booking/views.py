import datetime

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from gsr_booking.api_wrapper import APIError, LibCalWrapper, WhartonLibWrapper
from gsr_booking.booking_logic import book_rooms_for_group
from gsr_booking.csrfExemptSessionAuthentication import CsrfExemptSessionAuthentication
from gsr_booking.models import (
    GSR,
    Group,
    GroupMembership,
    GSRBooking,
    GSRBookingCredentials,
    UserSearchIndex,
)
from gsr_booking.serializers import (
    GroupBookingRequestSerializer,
    GroupMembershipSerializer,
    GroupSerializer,
    GSRBookingCredentialsSerializer,
    GSRBookingSerializer,
    GSRSerializer,
    UserSerializer,
)


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
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
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
        if username == "me":
            username = request.user.username

        user = get_object_or_404(User, username=username)
        return Response(
            GroupMembershipSerializer(
                GroupMembership.objects.filter(
                    user=user, accepted=False, group__in=self.request.user.booking_groups.all(),
                ),
                many=True,
            ).data
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, username=None):
        """
        Activate a user's account. Must be run when a user signs in for the first time, at least.
        The action is idempotent, so no harm in calling it multiple times.
        """
        if username == "me":
            username = request.user.username

        user = get_object_or_404(User, username=username)
        if user != request.user:
            return HttpResponseForbidden()

        # Ensure that all invites for this user, even ones created before their account was in the
        # DB, are associated with the User object.
        GroupMembership.objects.filter(username=user.username).update(user=user)

        UserSearchIndex.objects.get_or_create(user=user)

        return Response({"success": True})

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search the database of registered users by name or pennkey. Deprecated in favor
        of the platform route.
        """
        query = request.query_params.get("q", "")
        results = UserSearchIndex.objects.filter(
            Q(full_name__istartswith=query) | Q(pennkey__istartswith=query)
        ).select_related("user")

        return Response(UserSerializer([entry.user for entry in results], many=True).data)


class GSRBookingCredentialsViewSet(generics.RetrieveUpdateAPIView, generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = GSRBookingCredentialsSerializer

    def get_object(self):
        if not self.request.user.is_authenticated:
            return GSRBookingCredentials.objects.none()
        try:
            return GSRBookingCredentials.objects.get(user=self.request.user)
        except GSRBookingCredentials.DoesNotExist:
            if self.request.method == "PUT":
                return GSRBookingCredentials(user=self.request.user)
            else:
                raise Http404("detail not found")

    def update(self, *args, **kwargs):
        supplied_username = args[0].data.get("user")
        if supplied_username is None:
            return Response(data={"user": "not supplied"}, status=404)
        if self.request.user.username != supplied_username:
            return HttpResponseForbidden()
        return super().update(*args, **kwargs)


class GroupMembershipViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "group"]
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
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

    def create(self, request, *args, **kwargs):
        group_id = request.data.get("group")
        group = get_object_or_404(Group, pk=group_id)
        if not group.has_member(request.user):
            return HttpResponseForbidden()

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    def invite(self, request):
        """
        Invite a user to a group.
        """
        group_id = request.data.get("group")
        group = get_object_or_404(Group, pk=group_id)

        if not group.has_member(request.user):
            return HttpResponseForbidden()

        usernames = request.data.get("user").split(",")
        if isinstance(usernames, str):
            usernames = [usernames]

        for username in usernames:
            if GroupMembership.objects.filter(
                username=username, group=group, accepted=False
            ).exists():
                return Response({"message": "invite exists"}, status=400)
            elif GroupMembership.objects.filter(
                username=username, group=group, accepted=True
            ).exists():
                return Response({"message": f"user {username} already member"}, status=400)
            GroupMembership.objects.create(
                username=username, group=group, type=request.data.get("type", "M")
            )

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

    @action(detail=False, methods=["post"])
    def pennkey(self, request):
        group_id = request.data.get("group")
        username = request.data.get("user")
        allow = request.data.get("allow")
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(username=username)
        membership = GroupMembership.objects.get(user=user, group=group)
        membership.pennkey_allow = allow
        membership.save()
        return Response(
            {
                "message": "pennkey allowance updated",
                "user": membership.user.username,
                "group": membership.group_id,
            }
        )

    @action(detail=False, methods=["post"])
    def notification(self, request):
        group_id = request.data.get("group")
        username = request.data.get("user")
        active = request.data.get("active")
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(username=username)
        membership = GroupMembership.objects.get(user=user, group=group)
        membership.notifications = active
        membership.save()
        return Response(
            {
                "message": "notification updated",
                "user": membership.user.username,
                "group": membership.group_id,
            }
        )


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

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

    @action(detail=True, methods=["get"])
    def invites(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        if not group.has_member(request.user):
            return HttpResponseForbidden()

        return Response(
            GroupMembershipSerializer(
                GroupMembership.objects.filter(group=group, accepted=False), many=True
            ).data
        )

    @action(detail=True, methods=["post"], url_path="book-rooms")
    def book_rooms(self, request, pk):
        """
        Book GSR room(s) for a group. Requester must be an admin to book.
        """
        booking_serialized = GroupBookingRequestSerializer(data=request.data)
        if not booking_serialized.is_valid():
            return Response(status=400)

        booking_data = booking_serialized.data

        group = get_object_or_404(Group, pk=pk)

        # must be admin (and also a member) of the group to book
        if not group.has_admin(request.user):
            return HttpResponseForbidden()

        result_json = book_rooms_for_group(
            group, booking_data["room_bookings"], request.user.username
        )

        return Response(result_json)


# classes used for accessing GSR API's (needed for token authentication)
LCW = LibCalWrapper()
WLW = WhartonLibWrapper()


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
            .order_by("-end")[:2]
            .values_list("gsr", flat=True)
        )


class Availability(APIView):
    """
    Returns JSON containing all rooms for a given building.
    Usage:
        /studyspaces/availability/<building> gives all rooms for the next 24 hours
        /studyspaces/availability/<building>?start=2018-25-01 gives all rooms in the start date
        /studyspaces/availability/<building>?start=...&end=... gives all rooms between the two days
    """

    def get(self, request, lid, gid):

        start = request.GET.get("start")
        end = request.GET.get("end")
        # checks which GSR class to use
        if not GSR.objects.filter(lid=lid).exists():
            return Response({"error": "Unknown GSR"}, status=404)
        is_wharton = GSR.objects.filter(lid=lid).first().kind == GSR.KIND_WHARTON
        if is_wharton:
            try:
                if request.user.is_anonymous:
                    return Response({"error": "Anonymous User"}, status=400)
                # no need for gid under Wharton API
                rooms = WLW.get_availability(lid, start, end, request.user.username)
            except APIError as e:
                return Response({"error": str(e)}, status=400)
            gsr = GSR.objects.get(lid=lid)
            return Response({"name": gsr.name, "gid": gsr.gid, "rooms": rooms})
        else:
            try:
                rooms = LCW.get_availability(lid, start, end)
            except APIError as e:
                return Response({"error": str(e)}, status=400)

            # cleans data to match Wharton wrapper
            try:
                gsr = [x for x in rooms["categories"] if x["cid"] == int(gid)][0]
            except IndexError:
                return Response({"error": "Unknown GSR"}, status=404)

            for room in gsr["rooms"]:
                for availability in room["availability"]:
                    availability["start_time"] = availability["from"]
                    availability["end_time"] = availability["to"]
                    del availability["from"]
                    del availability["to"]
            context = {}
            context["name"] = gsr["name"]
            context["gid"] = gsr["cid"]
            context["rooms"] = [
                {"room_name": x["name"], "id": x["id"], "availability": x["availability"]}
                for x in gsr["rooms"]
            ]
            return Response(context)


class BookRoom(APIView):
    """Books room in any GSR in the availability route"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        start = request.data["start_time"]
        end = request.data["end_time"]
        if not GSR.objects.filter(gid=request.data["gid"]).exists():
            return Response({"error": "Unknown GSR"}, status=404)
        is_wharton = GSR.objects.filter(gid=request.data["gid"]).first().kind == GSR.KIND_WHARTON
        room_id = request.data["id"]
        room_name = request.data["room_name"]
        # checks which GSR class to use
        if is_wharton:
            try:
                booking_id = WLW.book_room(room_id, start, end, request.user.username)["booking_id"]
            except APIError as e:
                return Response({"error": str(e)}, status=400)
        else:
            try:
                booking_id = LCW.book_room(room_id, start, end, request.user)["booking_id"]
            except APIError as e:
                return Response({"error": str(e)}, status=400)
        # creates booking on database
        GSRBooking.objects.create(
            user=request.user,
            booking_id=str(booking_id),
            gsr=GSR.objects.get(gid=request.data["gid"]),
            room_id=room_id,
            room_name=room_name,
            start=datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z"),
            end=datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z"),
        )
        return Response({"detail": "success"})


class CancelRoom(APIView):
    """
    Cancels  a room for a given user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        booking_id = str(request.data["booking_id"])

        # gets list of all reservations from wharton
        # if student is non-wharton, then they will never
        # have reservations from wharton
        # throws error iff the error isn't just unable to
        # perform action
        try:
            wharton_bookings = WLW.get_reservations(request.user)["bookings"]
        except APIError as e:
            if str(e) == "Wharton: GSR view restricted to Wharton Pennkeys":
                wharton_bookings = []
            else:
                return Response({"error": str(e)}, status=400)
        wharton_booking_ids = [str(x["booking_id"]) for x in wharton_bookings]
        # checks if the booking_id is a wharton booking_id
        if booking_id not in wharton_booking_ids:
            gsr_booking = get_object_or_404(GSRBooking, booking_id=booking_id)
            if request.user != gsr_booking.user:
                return Response(
                    {"error": "Unauthorized: This reservation was booked by someone else."},
                    status=400,
                )
            else:
                # checks which GSR class to use
                is_wharton = False
        else:
            # defaults to wharton because it is in wharton_booking_ids
            wharton_booking = GSRBooking.objects.filter(booking_id=booking_id)
            if wharton_booking.exists():
                gsr_booking = wharton_booking.first()
            else:
                gsr_booking = None
            is_wharton = True

        if is_wharton:
            try:
                WLW.cancel_room(request.user, booking_id)
            except APIError as e:
                return Response({"error": str(e)}, status=400)
        else:
            try:
                LCW.cancel_room(booking_id)
            except APIError as e:
                return Response({"error": str(e)}, status=400)

        if gsr_booking:
            # updates GSR booking after done
            gsr_booking.is_cancelled = True
            gsr_booking.save()
        return Response({"detail": "success"})


class ReservationsView(APIView):
    """
    Gets reservations for a User
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = GSRBookingSerializer(
            GSRBooking.objects.filter(
                user=self.request.user, end__gte=timezone.localtime(), is_cancelled=False
            ),
            many=True,
        )
        response = serializer.data
        try:
            # ignore this because this route is used by everyone
            wharton_reservations = WLW.get_reservations(request.user)["bookings"]
            for reservation in wharton_reservations:
                if reservation["lid"] == 1:
                    reservation["lid"] = "JMHH"
                if reservation["lid"] == 6:
                    reservation["lid"] = "ARB"
                # checks if reservation is within time range
                if (
                    datetime.datetime.strptime(reservation["end"], "%Y-%m-%dT%H:%M:%S%z")
                    >= timezone.localtime()
                ):
                    # filtering for lid here works because Wharton buildings have distinct lid's
                    context = {
                        "booking_id": str(reservation["booking_id"]),
                        "gsr": GSRSerializer(GSR.objects.get(lid=reservation["lid"])).data,
                        "room_id": reservation["rid"],
                        "room_name": reservation["room"],
                        "start": reservation["start"],
                        "end": reservation["end"],
                    }
                    if context not in response:
                        response.append(context)
        except APIError:
            pass
        return Response(response)


class CheckWharton(APIView):
    def get(self, request):
        return Response({"is_wharton": WLW.is_wharton(request.user.username)})
