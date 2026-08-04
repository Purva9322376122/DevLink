"""
Chat business logic and services.
"""
from django.db.models import Q
from django.contrib.auth.models import User

from .models import Message


def create_message(sender: User, receiver: User, content: str, 
                  file_url: str = None, file_type: str = None) -> Message:
    """Create a new message between two users."""
    return Message.objects.create(
        sender=sender,
        receiver=receiver,
        content=content,
        file_url=file_url,
        file_type=file_type,
        is_delivered=False,
    )


def mark_message_delivered(message_id: int) -> Message:
    """Mark a message as delivered."""
    msg = Message.objects.filter(id=message_id).first()
    if msg:
        msg.mark_delivered()
    return msg


def mark_message_read(message_id: int) -> Message:
    """Mark a message as read."""
    msg = Message.objects.filter(id=message_id).first()
    if msg:
        msg.mark_read()
    return msg


def mark_conversation_read(user: User, other_user: User) -> int:
    """Mark all messages in a conversation as read. Returns count."""
    return Message.objects.filter(
        receiver=user,
        sender=other_user,
        is_read=False
    ).update(is_read=True)


def get_connection_check(user1: User, user2: User) -> bool:
    """Check if two users are connected (can message)."""
    from .models import Connection
    return Connection.objects.filter(
        Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
    ).exists()
