from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from gsr_booking.models import Group, GroupMembership, UserSearchIndex
from gsr_booking.serializers import GroupMembershipSerializer, GroupSerializer, UserSerializer


User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().prefetch_related(
        Prefetch('booking_groups', Group.objects.filter(groupmembership__accepted=True))
    )
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    lookup_field = 'username'

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'first_name', 'last_name']

    @action(detail=True, methods=['get'])
    def invites(self, request, username=None):
        user = get_object_or_404(User, username=username)
        return Response(
            GroupMembershipSerializer(GroupMembership.objects.filter(user=user, accepted=False), many=True).data
        )

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        results = UserSearchIndex.objects.filter(full_name__istartswith=query).select_related('user')
        return Response(UserSerializer([entry.user for entry in results], many=True).data)


class GroupMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'group']
    permission_classes = [IsAuthenticated]

    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'memberships'):
            return GroupMembership.objects.none()
        return self.request.user.memberships.all()

    @action(detail=False, methods=['post'])
    def invite(self, request):
        group_id = request.data.get('group')
        group = get_object_or_404(Group, pk=group_id)

        if not group.has_member(request.user):
            return HttpResponseForbidden()

        usernames = request.data.get('user').split(',')
        if isinstance(usernames, str):
            usernames = [usernames]

        for username in usernames:
            user = User.objects.get(username=username)
            if GroupMembership.objects.filter(user=user, group=group, accepted=False).exists():
                return Response({'message': 'invite exists'}, status=400)
            elif GroupMembership.objects.filter(user=user, group=group, accepted=True).exists():
                return Response({'message': f'user {username} already member'}, status=400)
            GroupMembership.objects.create(user=user, group=group, type=request.data.get('type', 'M'))

        return Response({'message': 'invite(s) sent.'})

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        if membership.user != request.user:
            return HttpResponseForbidden()

        membership.accepted = True
        membership.save()
        return Response({'message': 'group joined', 'user': membership.user.username, 'group': membership.group_id})

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        if membership.user != request.user:
            return HttpResponseForbidden()

        resp = {'message': 'invite declined', 'user': membership.user.username, 'group': membership.group_id}
        membership.delete()
        return Response(resp)

    @action(detail=False, methods=['post'])
    def pennkey(self, request):
        group_id = request.data.get('group')
        username = request.data.get('user')
        allow = request.data.get('allow')
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(username=username)
        membership = GroupMembership.objects.get(user=user, group=group)
        membership.pennkey_allow = allow
        membership.save()
        return Response({
            'message': 'pennkey allowance updated',
            'user': membership.user.username,
            'group': membership.group_id
        })

    @action(detail=False, methods=['post'])
    def notification(self, request):
        group_id = request.data.get('group')
        username = request.data.get('user')
        active = request.data.get('active')
        print(active)
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(username=username)
        membership = GroupMembership.objects.get(user=user, group=group)
        membership.notifications = active
        membership.save()
        return Response({
            'message': 'notification updated',
            'user': membership.user.username,
            'group': membership.group_id
        })


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Group.objects.none()
        return super().get_queryset()\
            .filter(members=self.request.user)\
            .prefetch_related(
                Prefetch('members', User.objects.filter(memberships__accepted=True))
            )

    @action(detail=True, methods=['get'])
    def invites(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        if not group.has_member(request.user):
            return HttpResponseForbidden()

        return Response(
            GroupMembershipSerializer(GroupMembership.objects.filter(group=group, accepted=False), many=True).data
        )
