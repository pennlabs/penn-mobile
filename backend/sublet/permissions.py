from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Grants permission if the current user is a superuser.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser

    def has_permission(self, request, view):
        return request.user.is_superuser


class SubletOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow the owner of a Sublet to edit or delete it.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the Sublet.
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.subletter == request.user


class OfferOwnerPermission(permissions.BasePermission):
    """
    Custom permission to allow owner of an offer to delete it.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the Sublet.
        if request.method in permissions.SAFE_METHODS:
            # Check if the user owns the sublet
            return obj.subletter == request.user
        return obj.user == request.user
