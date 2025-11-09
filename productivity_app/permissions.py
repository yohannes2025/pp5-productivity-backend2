# productivity_app/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAssignedOrReadOnly(BasePermission):
    """
    Allows read-only access to anyone.
    Allows modification only if the user is authenticated

    and assigned to the task.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user in obj.assigned_users.all()


class IsSelfOrReadOnly(BasePermission):
    """
    Allows users to retrieve, update, 
    or delete their own user account only.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user


class IsOwnerOrReadOnly(BasePermission):
    """
    Allows users to edit/delete only their own related objects
    (e.g., profiles).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
