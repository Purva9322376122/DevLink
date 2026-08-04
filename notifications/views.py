from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .selectors import get_notifications, get_recent_notifications
from .services import mark_all_read, mark_notification_read, get_unread_count


@login_required
def notification_list(request):
    """Full notifications page."""
    notifications = get_notifications(request.user)
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': get_unread_count(request.user),
    })


@login_required
def notification_dropdown(request):
    """Partial for the navbar notification dropdown (AJAX) - minimal recent 4 notifications."""
    notifications = get_recent_notifications(request.user, limit=4)
    return render(request, 'notifications/notification_dropdown.html', {
        'notifications': notifications,
        'unread_count': get_unread_count(request.user),
    })


@login_required
@require_POST
def mark_read(request, pk: int):
    """Mark a single notification as read (AJAX POST)."""
    mark_notification_read(pk, request.user)
    return JsonResponse({'status': 'ok', 'unread_count': get_unread_count(request.user)})


@login_required
@require_POST
def mark_all_read_view(request):
    """Mark all notifications as read (AJAX POST)."""
    count = mark_all_read(request.user)
    return JsonResponse({'status': 'ok', 'marked': count, 'unread_count': 0})
