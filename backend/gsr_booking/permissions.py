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
        if view.action in ["create", "destroy"]:
            return request.user and request.user.is_authenticated

        return False

    def has_object_permission(self, request, view, obj):
        if view.action == "retrieve":
            return True

        # For destroy, must own the share code
        if view.action == "destroy":
            return obj.owner == request.user

        return False
