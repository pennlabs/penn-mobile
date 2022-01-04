from rest_framework import permissions

from portal.logic import get_user_clubs
from portal.models import Poll


class IsSuperUser(permissions.BasePermission):
    """
    Grants permission if the current user is a superuser.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser

    def has_permission(self, request, view):
        return request.user.is_superuser


class PollOwnerPermission(permissions.BasePermission):
    """Permission that checks authentication and only permits owner to update/destroy objects"""

    def has_object_permission(self, request, view, obj):
        # only creator can edit
        if view.action in ["partial_update", "update", "destroy"]:
            return obj.club_code in [x["club"]["code"] for x in get_user_clubs(request.user)]
        return True

    def has_permission(self, request, view):
        return request.user.is_authenticated


class OptionOwnerPermission(permissions.BasePermission):
    """Permission that checks authentication and only permits owner of Poll to update
    corresponding Option objects"""

    def has_object_permission(self, request, view, obj):
        # only creator can edit
        if view.action in ["partial_update", "update", "destroy"]:
            return obj.poll.club_code in [x["club"]["code"] for x in get_user_clubs(request.user)]
        return True

    def has_permission(self, request, view):
        # only creator of poll can create poll option
        if view.action == "create" and request.data:
            poll = Poll.objects.get(id=request.data["poll"])
            return poll.club_code in [x["club"]["code"] for x in get_user_clubs(request.user)]
        return request.user.is_authenticated


class TimeSeriesPermission(permissions.BasePermission):
    """Permission that checks for Time Series access (only creator of Poll and admins)"""

    def has_permission(self, request, view):
        poll = Poll.objects.filter(id=view.kwargs["id"])
        # checks if poll exists
        if poll.exists():
            # only poll creator and admin can access
            return poll.first().club_code in [
                x["club"]["code"] for x in get_user_clubs(request.user)
            ]
        return False


class PostOwnerPermission(permissions.BasePermission):
    """checks authentication and only permits owner to update/destroy posts"""

    def has_object_permission(self, request, view, obj):
        # only creator can edit
        if view.action in ["partial_update", "update", "destroy"]:
            return request.user == obj.user
        return True

    def has_permission(self, request, view):
        return request.user.is_authenticated
