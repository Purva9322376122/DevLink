"""
Core DRF permission classes.

These are used across all apps. Import them as:
    from core.permissions import IsOwner, IsOwnerOrReadOnly, IsConnected, IsPublic
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Allow read access to anyone; write access only to the object owner.
    The object must have a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return hasattr(obj, 'user') and obj.user == request.user


class IsOwner(BasePermission):
    """
    Allow access only to the owner of the object.
    No read access for non-owners.
    The object must have a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'user') and obj.user == request.user


class IsConnected(BasePermission):
    """
    Allow access only if the requesting user is connected (has a Connection
    record) with the target user identified by `username` in the URL kwargs.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        target_username = view.kwargs.get('username')
        if not target_username:
            return False

        from django.db.models import Q
        from opportunities.models import Connection

        return Connection.objects.filter(
            Q(user1=request.user, user2__username=target_username) |
            Q(user2=request.user, user1__username=target_username)
        ).exists()


class IsPublic(BasePermission):
    """Allow read-only access to everyone (authenticated or not)."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
