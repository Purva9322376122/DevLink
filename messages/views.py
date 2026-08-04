from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def start_conversation(request, username):
    """
    Check if a conversation already exists between request.user and target user.
    If yes, redirect to it.
    If not, create a new conversation and redirect to it.
    """
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        return redirect('messages:list')

    # Look for existing conversation between the two users
    conversation = (
        Conversation.objects.filter(participants=request.user)
        .filter(participants=target_user)
        .first()
    )

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, target_user)

    return redirect('messages:room', conversation_id=conversation.id)


@login_required
def message_list(request):
    """
    List conversations for the current user.
    If conversations exist, auto-select the latest active conversation.
    If no conversations exist, render the empty state.
    """
    conversations_qs = (
        request.user.direct_conversations
        .prefetch_related('participants', 'messages')
        .order_by('-created_at')
    )

    conversations = []
    for conv in conversations_qs:
        other_user = conv.participants.exclude(id=request.user.id).first()
        last_message = conv.messages.order_by('-timestamp').last() or conv.messages.order_by('-timestamp').first()
        unread_count = conv.messages.filter(is_read=False).exclude(sender=request.user).count()

        conv.other_user = other_user
        conv.last_message = last_message
        conv.unread_count = unread_count
        conversations.append(conv)

    conversations.sort(
        key=lambda c: c.last_message.timestamp if c.last_message else c.created_at,
        reverse=True
    )

    if conversations:
        return redirect('messages:room', conversation_id=conversations[0].id)

    return render(request, 'messages/message_list.html', {'conversations': []})


@login_required
def chat_room(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)

    # Ensure current user is a participant
    if not conv.participants.filter(id=request.user.id).exists():
        raise Http404()

    # Mark unread incoming messages as read
    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    # Handle POST message submission (AJAX or form POST)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            msg = Message.objects.create(
                conversation=conv,
                sender=request.user,
                content=content
            )

            # Return JSON response for AJAX requests
            if (
                request.headers.get('x-requested-with') == 'XMLHttpRequest' or
                'application/json' in request.headers.get('accept', '') or
                request.POST.get('is_ajax') == 'true'
            ):
                return JsonResponse({
                    'status': 'ok',
                    'message_id': msg.id,
                    'content': msg.content,
                    'sender': msg.sender.username,
                    'timestamp': 'Just now'
                })

            return redirect('messages:room', conversation_id=conv.id)

    # Pre-compute all conversations for left sidebar
    conversations_qs = (
        request.user.direct_conversations
        .prefetch_related('participants', 'messages')
        .order_by('-created_at')
    )

    conversations = []
    for c in conversations_qs:
        other_u = c.participants.exclude(id=request.user.id).first()
        last_msg = c.messages.order_by('-timestamp').last() or c.messages.order_by('-timestamp').first()
        unread_cnt = c.messages.filter(is_read=False).exclude(sender=request.user).count()

        c.other_user = other_u
        c.last_message = last_msg
        c.unread_count = unread_cnt
        conversations.append(c)

    conversations.sort(
        key=lambda c: c.last_message.timestamp if c.last_message else c.created_at,
        reverse=True
    )

    other_user = conv.participants.exclude(id=request.user.id).first()
    conv.other_user = other_user

    messages = conv.messages.select_related('sender').all().order_by('timestamp')

    return render(request, 'messages/chat_room.html', {
        'conversation': conv,
        'conversations': conversations,
        'chat_messages': messages,
    })