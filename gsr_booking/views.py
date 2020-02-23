import requests
import datetime
import math

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from gsr_booking.csrfExemptSessionAuthentication import CsrfExemptSessionAuthentication
from gsr_booking.models import Group, GroupMembership, UserSearchIndex
from gsr_booking.serializers import (
    GroupMembershipSerializer,
    GroupSerializer,
    UserSerializer,
    GroupBookingRequestSerializer,
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
                    user=user, accepted=False, group__in=self.request.user.booking_groups.all()
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
        return self.request.user.memberships.all()

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
            return Response({"message": "invite has alredy been accepted"}, 400)

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
        print(active)
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

    @action(detail=True, methods=["post"], url_path="book-room")
    def book_room(self, request, pk):
        request.data.update({"group_id": pk})
        booking_serialized = GroupBookingRequestSerializer(data=request.data)
        if not booking_serialized.is_valid():
            return Response(status=400)

        booking_data = booking_serialized.data

        # parameters: roomid, startTime, endTime, lid, sessionid
        group = get_object_or_404(Group, pk=booking_data["group_id"])
        if not group.has_member(request.user) or not group.is_admin(request.user):
            return HttpResponseForbidden()

        result_json = self.book_room_for_group(group, booking_data['is_wharton'], booking_data['room'], booking_data['lid'], booking_data['start'], booking_data['end'])

        return Response(result_json)

    def book_room_for_group(self, group, is_wharton, room, lid, start, end):
        # makes a request to labs api server to book rooms, and returns result json if successful
        if is_wharton:  # huntsman reservation
            pennkey_active_members = group.get_pennkey_active_members()

            return {"success": False, "error": "Unable to book huntsman rooms yet"}
        else:  # lib reservation
           
            #Find the first timeslot to book for (next_start, next_end)
            DATE_FORMAT_STR = "%Y-%m-%dT%H:%M:%S%z"
            START_DATE = datetime.datetime.strptime(start, DATE_FORMAT_STR)
            END_DATE = datetime.datetime.strptime(end, DATE_FORMAT_STR)
            MAX_SLOT_HRS = 1.5  # the longest booking allowed per person (should be 1.5 hrs)
            MIN_SLOT_HRS = 0.5  # the minimum booking allowed per person
            next_start = START_DATE
            next_end = min(END_DATE, next_start + datetime.timedelta(hours=MAX_SLOT_HRS))

            # loop through each member, and attempt to book on their behalf
            members = group.get_pennkey_active_members()
            bookings = {}
            failed_members = []  #store the members w/ failed bookings in here
            for member in members:
                if next_end - next_start < datetime.timedelta(hours=0.1):
                    print("BOOKED EVERYTHING ALREADY")
                    break
                if member.user.email is "":
                    print("*User " + member.username + " had an empty email")
                    continue

                # make request to labs-api-server
                success = self.book_room_for_user(
                    room,
                    lid,
                    next_start.strftime(DATE_FORMAT_STR),
                    next_end.strftime(DATE_FORMAT_STR),
                    member.user.email,
                )
                if success:
                    key = f'{lid}_{room}' 
                    booking_obj = {
                        'start': next_start.strftime(DATE_FORMAT_STR), 
                        'end': next_end.strftime(DATE_FORMAT_STR), 
                        'pennkey': member.username,
                        'booked': True
                    }
                    if not key in bookings:
                        bookings[key] = []
                    bookings[key].append(booking_obj)
                    # successful_bookings.append({
                    #     'lid': lid, 
                    #     'room': room, 
                    #     'bookings': [
                    #         {
                    #             'start': next_start.strftime(DATE_FORMAT_STR), 
                    #             'end': next_end.strftime(DATE_FORMAT_STR), 
                    #             'pennkey': member.username,
                    #             'booked': True
                    #         }
                    #     ]
                    #     })
                    
                    next_start = next_end
                    next_end = min(END_DATE, next_start + datetime.timedelta(hours=MAX_SLOT_HRS))
                    print("Succeeded!")
                else:
                    failed_members.append(member)
                    print("Failed :(")

            print("*Attempting to rebook failed slots now (if any)")

            # if unbooked slots still remain and not all booking requests succeeded, loop through each member again
            # if credits > 0, then book as much of nextSlot as possible
            # if slot successfully booked, move nextSlot ahead appropriately
            
            for member in failed_members:
                if next_end - next_start < datetime.timedelta(hours=0.1):
                    print("BOOKED EVERYTHING ALREADY")
                    break
                if member.user.email is "":
                    print("empty email address")
                    continue

                # calculate number of credits already used via getReservations
                (success, used_credit_hours) = self.get_used_booking_credit_for_user(
                    lid, member.user.email, DATE_FORMAT_STR
                )
                remaining_credit_hours = MAX_SLOT_HRS - used_credit_hours
                rounded_remaining_credit_hours = math.floor(2 * remaining_credit_hours) / 2
                print(f"Found ", rounded_remaining_credit_hours, " remaining booking hrs!")
                if success and remaining_credit_hours >= MIN_SLOT_HRS:
                    
                    next_end = min(
                        END_DATE,
                        next_start + datetime.timedelta(hours=rounded_remaining_credit_hours),
                    )
                    success = self.book_room_for_user(
                        room,
                        lid,
                        next_start.strftime(DATE_FORMAT_STR),
                        next_end.strftime(DATE_FORMAT_STR),
                        member.user.email,
                    )
                    if success:
                        key = f'{lid}_{room}' 
                        booking_obj = {
                            'start': next_start.strftime(DATE_FORMAT_STR), 
                            'end': next_end.strftime(DATE_FORMAT_STR), 
                            'pennkey': member.username,
                            'booked': True
                        }
                        if not key in bookings:
                            bookings[key] = []
                        bookings[key].append(booking_obj)

                        next_start = next_end
                        next_end = min(
                            END_DATE, next_start + datetime.timedelta(hours=MAX_SLOT_HRS)
                        )
                        print("Suceeded!")
                    else:
                        print("Failed :(")

            complete_success = next_end - next_start < datetime.timedelta(hours=0.1)
            partial_success = (len(bookings) > 0)
            result_json = {
                "complete_success": success,
                "partial_success": partial_success,
                "rooms": []#,
                # "fromDate": START_DATE.strftime(DATE_FORMAT_STR),
                # "toDate": next_start.strftime(DATE_FORMAT_STR)
            }
            for (key, bookings_array) in bookings.items():
                key_split = key.split('_')
                lid = key_split[0]
                room = key_split[1]
                result_json['rooms'].append({
                    'lid': lid,
                    'room': room,
                    'bookings': bookings_array
                })

            return result_json

    def get_used_booking_credit_for_user(self, lid, email, DATE_FORMAT_STR):
        # returns a user's used booking credit (in hours) for a specific building (lid)
        RESERVATIONS_URL = "https://api.pennlabs.org/studyspaces/reservations"
        if lid == "1":
            return (False, 0)  # doesn't support huntsman yet
        try:
            print(f"*Attempting to get reservation credits for {email:s}")
            r = requests.get(RESERVATIONS_URL + "?email=" + email)
            if r.status_code == 200:
                resp_data = r.json()
                reservations = resp_data["reservations"]
                used_credit_hours = 0
                for reservation in reservations:
                    from_date = datetime.datetime.strptime(reservation["fromDate"], DATE_FORMAT_STR)
                    to_date = datetime.datetime.strptime(reservation["toDate"], DATE_FORMAT_STR)
                    reservation_hours = (to_date - from_date).total_seconds() / 3600
                    if str(reservation["lid"]) == lid and reservation_hours > 0.1:
                        used_credit_hours += reservation_hours
                return (True, used_credit_hours)
        except requests.exceptions.RequestException as e:
            print(e)
        return (False, 0)

    def book_room_for_user(self, room, lid, start, end, email):
        # tries to make a booking for an individual user, and returns success or not
        if lid is "1":
            return False  # does not support huntsman booking yet
        print(f"*Attempting to book room {room:d} from {start:s} to {end:s} via {email:s}")
        BOOKING_URL = "https://api.pennlabs.org/studyspaces/book"
        form_data = {
            "firstname": "Group GSR User",
            "lastname": "Group GSR User",
            "groupname": "Group GSR",
            "size": "2-3",
            "phone": "2158986533",
            "room": room,
            "lid": lid,
            "start": start,
            "end": end,
            "email": email,
        }

        try:
            r = requests.post(BOOKING_URL, data=form_data)
            if r.status_code == 200:
                resp_data = r.json()
                if "error" in resp_data and resp_data["error"] is not None:
                    print("error: " + resp_data["error"])
                return resp_data["results"]
        except requests.exceptions.RequestException as e:
            print("error: " + str(e))
        return False

    def make_booking_request_huntsman(self, roomid, startTime, endTime, lid, sessionid):
        # makes a request to labs api server to book rooms, and returns result json if successful
        booking_url = "https://api.pennlabs.org/studyspaces/book"
        if lid == "1":
            return {"success": False, "error": "Unable to book huntsman rooms yet"}
        form_data = {
            "room": roomid,
            "start": startTime,
            "end": endTime,
            "lid": lid,
            "sessionid": sessionid,
        }

        # catch potential error in request
        result = {}
        try:
            r = requests.post(booking_url, data=form_data)
        except requests.exceptions.RequestException as e:
            print("error: " + str(e))
            result["error"] = str(e)
            result["success"] = False

        # go through all of them, do it in 90 minute slots. if it fails, see if anyone has

        # construct result json
        if "r" in locals() and r.status_code == 200:
            resp_data = r.json()
            print(resp_data)
            result["success"] = resp_data["results"]
            if "error" in resp_data:
                result["error"] = resp_data["error"]
        else:
            result["success"] = False
            result["error"] = "Call to labs-api-server failed"

        return result
