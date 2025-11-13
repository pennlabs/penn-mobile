from rest_framework import permissions


class IsShareCodeOwner(permissions.BasePermission):
    """
    Custom permission to allow only the owner of a share code to delete it.
    Similar to SubletOwnerPermission pattern.
    """

    def has_permission(self, request, view):
        # For retrieve action, allow anyone
        if view.action == "retrieve":
            return True

        # For create/destroy, require authentication
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        booking = obj.booking
        owner = booking.reservation.creator if booking.reservation else booking.user

        # Allow safe methods (GET) for anyone if valid
        if request.method in permissions.SAFE_METHODS:
            return obj.is_valid()

        # For DELETE, must be owner
        is_owner = owner == request.user
        if not is_owner:
            return False
        return True
