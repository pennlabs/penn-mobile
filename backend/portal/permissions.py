from typing import Any, cast

from rest_framework import permissions
from rest_framework.request import Request

from portal.logic import get_user_clubs
from portal.models import Poll, PollOption
from utils.types import get_auth_user


class IsSuperUser(permissions.BasePermission):
    """
    Grants permission if the current user is a superuser.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return get_auth_user(request).is_superuser

    def has_permission(self, request: Request, view: Any) -> bool:
        return get_auth_user(request).is_superuser


class PollOwnerPermission(permissions.BasePermission):
    """Permission that checks authentication and only permits owner to update/destroy objects"""

    def _get_club_code(self, obj: Any) -> str:
        """Helper to get club_code from either Poll or PollOption object"""
        if isinstance(obj, Poll):
            return obj.club_code
        elif isinstance(obj, PollOption):
            poll = cast(Poll, obj.poll)
            return poll.club_code
        raise ValueError(f"Unexpected object type: {type(obj)}")

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # only creator can edit
        user = get_auth_user(request)
        if view.action in ["partial_update", "update", "destroy"]:
            club_code = self._get_club_code(obj)
            return club_code in [x["club"]["code"] for x in get_user_clubs(user)]
        return user.is_authenticated

    def has_permission(self, request: Request, view: Any) -> bool:
        return get_auth_user(request).is_authenticated


class OptionOwnerPermission(permissions.BasePermission):
    """Permission that checks authentication and only permits owner of Poll to update
    corresponding Option objects"""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # only creator can edit
        user = get_auth_user(request)
        if view.action in ["partial_update", "update", "destroy"]:
            return obj.poll.club_code in [x["club"]["code"] for x in get_user_clubs(user)]
        return True

    def has_permission(self, request: Request, view: Any) -> bool:
        # only creator of poll can create poll option
        user = get_auth_user(request)
        if view.action == "create" and request.data:
            poll = Poll.objects.get(id=request.data["poll"])
            return poll.club_code in [x["club"]["code"] for x in get_user_clubs(user)]
        return user.is_authenticated


class TimeSeriesPermission(permissions.BasePermission):
    """Permission that checks for Time Series access (only creator of Poll and admins)"""

    def has_permission(self, request: Request, view: Any) -> bool:
        poll = Poll.objects.filter(id=view.kwargs["poll_id"]).first()
        user = get_auth_user(request)
        # checks if poll exists
        if poll is not None:
            # only poll creator and admin can access
            return poll.club_code in [x["club"]["code"] for x in get_user_clubs(user)]
        return False


class PostOwnerPermission(permissions.BasePermission):
    """checks authentication and only permits owner to update/destroy posts"""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # only creator can edit
        user = get_auth_user(request)
        if view.action in ["partial_update", "update", "destroy"]:
            return obj.club_code in [x["club"]["code"] for x in get_user_clubs(user)]
        return True

    def has_permission(self, request: Request, view: Any) -> bool:
        return request.user.is_authenticated
