"""
Notifications selectors — read-only query helpers.
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import QuerySet


def get_notifications(user: User, unread_only: bool = False) -> QuerySet:
    """Return all (or only unread) notifications for a user, newest first."""
    from .models import Notification
    qs = Notification.objects.filter(recipient=user).select_related(
        'actor', 'actor__profile'
    )
    if unread_only:
        qs = qs.filter(is_read=False)
    return qs


def get_recent_notifications(user: User, limit: int = 10) -> QuerySet:
    """Return the most recent N notifications for navbar dropdown."""
    return get_notifications(user)[:limit]
