"""
Opportunities selectors — read-only query functions for the opportunities app.
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import Q

from .models import Message


def get_conversations(user: User) -> list[dict]:
    """
    Return a list of conversation dicts for the messages list view.

    Each dict contains keys expected by the templates:
        user             — the other participant (User instance)
        last_message     — the most recent Message in the conversation
        unread_count     — number of unread messages from the other user
        is_online        — presence flag (False by default)
        profile_image_url— URL for the other user's avatar (safe fallback)
    """
    messages_qs = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).order_by('-timestamp').select_related('sender', 'receiver')

    conversations: list[dict] = []
    users_seen: set[int] = set()

    for msg in messages_qs:
        other_user = msg.receiver if msg.sender == user else msg.sender
        if other_user.id not in users_seen:
            unread_count = Message.objects.filter(
                sender=other_user,
                receiver=user,
                is_read=False,
            ).count()

            # Safe profile image fallback
            try:
                profile = getattr(other_user, 'profile')
            except Exception:
                profile = None

            if profile and getattr(profile, 'profile_image', None):
                try:
                    profile_image_url = profile.profile_image.url
                except Exception:
                    profile_image_url = f"https://ui-avatars.com/api/?name={other_user.username}&background=6366f1&color=ffffff&size=64"
            else:
                profile_image_url = f"https://ui-avatars.com/api/?name={other_user.username}&background=6366f1&color=ffffff&size=64"

            conversations.append({
                'user': other_user,
                'last_message': msg,
                'unread_count': unread_count,
                'is_online': False,  # presence system not implemented yet
                'profile_image_url': profile_image_url,
            })
            users_seen.add(other_user.id)

    # Sort by most recent message timestamp
    conversations.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else 0,
        reverse=True
    )

    return conversations[:20]
