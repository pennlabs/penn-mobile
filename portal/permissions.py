from rest_framework import permissions

from portal.models import Poll, PollOption


class OwnerPermission(permissions.BasePermission):
    """Permission that checks authentication and only permits owner to update/destroy objects"""

    def has_object_permission(self, request, view, obj):
        # only creator can edit
        if view.action in ["partial_update", "update", "destroy"]:
            if type(obj) == PollOption:
                return request.user == obj.poll.user or request.user.is_superuser
            return request.user == obj.user
        return True

    def has_permission(self, request, view):
        return request.user.is_authenticated


class TimeSeriesPermission(permissions.BasePermission):
    """Permission that checks for Time Series access (only creator of Poll and admins)"""

    def has_permission(self, request, view):
        poll = Poll.objects.filter(id=view.kwargs["id"])
        if poll.exists():
            return (
                poll.first().user == request.user and request.user.is_authenticated
            ) or request.user.is_superuser
        return False
