"""
Chat data selectors and queries.
"""
from typing import List, Tuple
from django.db.models import Q, Count, Max
from django.contrib.auth.models import User

from .models import Message


def get_messages_between(user1: User, user2: User, limit: int = 50, 
                        offset: int = 0) -> List[Message]:
    """
    Get messages between two users, ordered chronologically.
    Recent messages last (for pagination).
    """
    return Message.objects.filter(
        Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1)
    ).order_by('timestamp')[offset:offset + limit]


def get_unread_count(user: User, other_user: User = None) -> int:
    """Get count of unread messages for a user."""
    query = Message.objects.filter(receiver=user, is_read=False)
    if other_user:
        query = query.filter(sender=other_user)
    return query.count()


def get_conversations(user: User, limit: int = 20) -> List[Tuple[User, Message]]:
    """
    Get list of conversations for a user with the most recent message.
    Returns tuples of (other_user, last_message, unread_count).
    """
    # Find all distinct users this user has messaged with
    sent_to = Message.objects.filter(sender=user).values_list(
        'receiver_id', flat=True
    ).distinct()
    received_from = Message.objects.filter(receiver=user).values_list(
        'sender_id', flat=True
    ).distinct()
    
    all_user_ids = set(sent_to) | set(received_from)
    
    conversations = []
    for user_id in all_user_ids:
        other_user = User.objects.get(id=user_id)
        
        # Get last message
        last_msg = Message.objects.filter(
            Q(sender=user, receiver=other_user) | Q(sender=other_user, receiver=user)
        ).order_by('-timestamp').first()
        
        # Get unread count
        unread = Message.objects.filter(
            receiver=user,
            sender=other_user,
            is_read=False
        ).count()
        
        conversations.append({
            'other_user': other_user,
            'last_message': last_msg,
            'unread_count': unread,
        })
    
    # Sort by most recent message
    conversations.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else 0,
        reverse=True
    )
    
    return conversations[:limit]


def get_pinned_messages(user1: User, user2: User) -> List[Message]:
    """Get pinned messages in a conversation."""
    return Message.objects.filter(
        Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1),
        is_pinned=True
    ).order_by('-timestamp')


def search_messages(user: User, query: str, other_user: User = None) -> List[Message]:
    """Search messages containing the query text."""
    msg_query = Message.objects.filter(
        Q(sender=user, content__icontains=query) |
        Q(receiver=user, content__icontains=query)
    )
    
    if other_user:
        msg_query = msg_query.filter(
            Q(sender=user, receiver=other_user) |
            Q(sender=other_user, receiver=user)
        )
    
    return msg_query.order_by('-timestamp')
