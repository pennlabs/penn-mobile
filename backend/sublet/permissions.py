from typing import Any

from rest_framework import permissions
from rest_framework.request import Request

from utils.types import get_auth_user


class IsSuperUser(permissions.BasePermission):
    """
    Grants permission if the current user is a superuser.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return get_auth_user(request).is_superuser

    def has_permission(self, request: Request, view: Any) -> bool:
        return get_auth_user(request).is_superuser


class SubletOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow the owner of a Sublet to edit or delete it.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        return get_auth_user(request).is_authenticated

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # Check if the user is the owner of the Sublet.
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.subletter == get_auth_user(request)


class SubletImageOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow the owner of a SubletImage to edit or delete it.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        return get_auth_user(request).is_authenticated

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        # Check if the user is the owner of the Sublet.
        return request.method in permissions.SAFE_METHODS or obj.sublet.subletter == get_auth_user(
            request
        )


class OfferOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow owner of an offer to delete it.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        return get_auth_user(request).is_authenticated

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        if request.method in permissions.SAFE_METHODS:
            # Check if the user owns the sublet when getting list
            return obj.subletter == get_auth_user(request)
        # This is redundant, here for safety
        return obj.user == get_auth_user(request)
