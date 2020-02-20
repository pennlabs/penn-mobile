from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from gsr_booking.csrfExemptSessionAuthentication import CsrfExemptSessionAuthentication
from gsr_booking.models import Group, GroupMembership, UserSearchIndex
from gsr_booking.serializers import GroupMembershipSerializer, GroupSerializer, UserSerializer
from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests

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
        #parameters: roomid, startTime, endTime, lid, sessionid
        group = get_object_or_404(Group, pk=pk)
        if not group.has_member(request.user) or not group.is_admin(request.user):
            return HttpResponseForbidden()

        #extract params, check if some were not passed
        param_keys = ['room', 'start', 'end', 'lid']
        params = {}
        for field in param_keys:
            params[field] = request.data.get(field)
            if params[field] is None:
                return Response({
                    'success': False,
                    'error': field + ' is a missing parameter' 
                })
            if field == 'lid': #depending on reservation type, need to add extra params
                if params['lid'] == '1':
                    param_keys.append('sessionid')
                else:
                    param_keys.extend(['firstname', 'lastname', 'email', 'groupname', 'size', 'phone'])
            
        result_json = self.make_booking_request(group, params)

        
        return Response(
            result_json
        )

    def make_booking_request(self, group, params):
        #makes a request to labs api server to book rooms, and returns result json if successful
        booking_url = 'https://api.pennlabs.org/studyspaces/book' 
        if params['lid'] == "1": #huntsman reservation
            pennkey_active_members = group.get_pennkey_active_members()

            return {
                "success": False,
                "error": "Unable to book huntsman rooms yet"
            }
        else: #lib reservation
            #duplicating original params, in case naming conventions change (this method enables more flexibility)
            form_keys = ['room', 'start', 'end', 'lid', 'firstname', 'lastname', 'email', 'groupname', 'size', 'phone']
            form_data = {}
            for key in form_keys:
                form_data[key] = params[key] 
            
            #nextSlot <- find first slot (<= 90 min) to book for
            
            #loop through each member, and attempt to book 90 min on their behalf if pennkeyAllowed
                #if nextSlot successfully booked, then move nextSlot 90 min ahead or exit loop
            members = group.get_members()
            for member in members:
                pennkey = member.username
                #TODO: Obtain emails; don't take in emails as a param anymore

            #if unbooked slots still remain, loop through each member again
                #calculate number of credits (30-min slots) available (getReservations)
                #if credits > 0, then book as much of nextSlot as possible
                    #if slot successfully booked, move nextSlot ahead appropriately

            #if unbooked slots still remain, return all the successful bookings, and which ones didn't get booked


            #make request to labs-api-server
            result_json = {}
            try:
                r = requests.post(booking_url, data=form_data)
            except requests.exceptions.RequestException as e:
                print("error: " + str(e))
                result_json['error'] = str(e)
                result_json['success'] = False
                return result_json

            #
        #go through all of them, do it in 90 minute slots. if it fails, see if anyone has 
        

        #construct result json
        if ('r' in locals() and r.status_code == 200):
            resp_data = r.json()
            print(resp_data)
            result_json['success'] = resp_data['results']
            if 'error' in resp_data and resp_data['error'] is not None:
                result_json['error'] = resp_data['error']
        else:
            result_json['success'] = False
            result_json['error'] = "Call to labs-api-server failed"

        return result_json

    def make_booking_request_huntsman(self, roomid, startTime, endTime, lid, sessionid):
        #makes a request to labs api server to book rooms, and returns result json if successful
        booking_url = 'https://api.pennlabs.org/studyspaces/book' 
        if lid == "1":
            return {
                "success": False,
                "error": "Unable to book huntsman rooms yet"
            }
        form_data = {'room': roomid, 'start': startTime, 'end': endTime, 'lid': lid, 'sessionid': sessionid}
        
        #catch potential error in request
        result = {}
        try:
            r = requests.post(booking_url, data=form_data)
        except requests.exceptions.RequestException as e:
            print("error: " + str(e))
            result['error'] = str(e)
            result['success'] = False

        #go through all of them, do it in 90 minute slots. if it fails, see if anyone has 
        

        #construct result json
        if ('r' in locals() and r.status_code == 200):
            resp_data = r.json()
            print(resp_data)
            result['success'] = resp_data['results']
            if 'error' in resp_data:
                result['error'] = resp_data['error']
        else:
            result['success'] = False
            result['error'] = "Call to labs-api-server failed"

        return result
