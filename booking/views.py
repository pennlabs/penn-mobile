from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.http import Http404
from django.db.models import Prefetch

from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from booking.serializers import UserSerializer, GroupMembershipSerializer, GroupSerializer
from booking.models import GroupMembership, Group

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

    @action(detail=True, methods=['get'])
    def invites(self, request, username=None):
        user = get_object_or_404(User, username=username)
        return Response(
            GroupMembershipSerializer(GroupMembership.objects.filter(user=user, accepted=False), many=True).data)


class GroupMembershipViewSet(viewsets.ModelViewSet, mixins.CreateModelMixin):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'group']

    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer

    # def get_queryset(self):
    #     if self.request.user is None or not hasattr(self.request.user, 'memberships'):
    #         return GroupMembership.objects.none()
    #     return self.request.user.memberships.all()

    @action(detail=False, methods=['post'])
    def invite(self, request):
        group_id = request.data.get('group')
        username = request.data.get('user')
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(username=username)
        GroupMembership.objects.create(user=user, group=group, type=request.data.get('type', 'M'))

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)
        membership.accepted = True
        membership.save()
        return Response({'message': 'group joined', 'user': membership.user.username, 'group': membership.group_id})

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        membership = get_object_or_404(GroupMembership, pk=pk, accepted=False)

        resp = {'message': 'invite declined', 'user': membership.user.username, 'group': membership.group_id}
        membership.delete()
        return Response(resp)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_queryset(self):
        return super().get_queryset().prefetch_related(Prefetch('members', User.objects.filter(memberships__accepted=True)))

    @action(detail=True, methods=['get'])
    def invites(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        return Response(GroupMembershipSerializer(GroupMembership.objects.filter(group=group, accepted=False), many=True).data)

    # def get_queryset(self):
    #     if self.request.user is None or not hasattr(self.request.user, 'booking_groups'):
    #         return Group.objects.none()
    #     return self.request.user.booking_groups.all()

