"""
Notifications services — create, dispatch, and mark notifications.
"""
from __future__ import annotations

import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger('devlink')


def create_notification(
    recipient: User,
    actor: User | None,
    verb: str,
    target=None,
    target_url: str = '',
    preview: str = '',
) -> None:
    """
    Create a Notification record and push it to the recipient's
    WebSocket channel in real-time.

    This is safe to call from synchronous signal handlers.
    """
    from .models import Notification

    if recipient == actor:
        return  # never notify users of their own actions

    ct = None
    object_id = None
    if target is not None:
        ct = ContentType.objects.get_for_model(target)
        object_id = target.pk

    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        content_type=ct,
        object_id=object_id,
        target_url=target_url,
        preview=preview,
    )

    _push_to_websocket(notification)


def mark_notification_read(notification_id: int, user: User) -> bool:
    """Mark a single notification as read. Returns True if updated."""
    from .models import Notification
    updated = Notification.objects.filter(
        id=notification_id, recipient=user, is_read=False
    ).update(is_read=True)
    return updated > 0


def mark_all_read(user: User) -> int:
    """Mark all unread notifications for a user as read. Returns count."""
    from .models import Notification
    count = Notification.objects.filter(
        recipient=user, is_read=False
    ).update(is_read=True)
    return count


def get_unread_count(user: User) -> int:
    from .models import Notification
    return Notification.objects.filter(recipient=user, is_read=False).count()


def _push_to_websocket(notification) -> None:
    """Push a notification event to the user's personal WebSocket group."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        group_name = f"notifications_{notification.recipient_id}"
        actor_username = (
            notification.actor.username if notification.actor else 'System'
        )
        actor_avatar = ''
        if notification.actor:
            try:
                actor_avatar = notification.actor.profile.profile_image.url
            except Exception:
                actor_avatar = ''

        payload = {
            'type': 'notification_new',
            'id': notification.id,
            'verb': notification.verb,
            'actor_username': actor_username,
            'actor_avatar': actor_avatar,
            'target_url': notification.target_url,
            'preview': notification.preview,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
        }

        async_to_sync(channel_layer.group_send)(group_name, payload)
        logger.debug("Notification pushed to %s", group_name)

    except Exception as exc:
        # Never let a WebSocket failure break the request flow
        logger.warning("WebSocket push failed for notification %s: %s", notification.id, exc)
