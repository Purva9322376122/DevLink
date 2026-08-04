def unread_notifications(request):
    """Inject unread_notification_count into every template context."""
    if not request.user.is_authenticated:
        return {'unread_notification_count': 0}
    from notifications.services import get_unread_count
    return {'unread_notification_count': get_unread_count(request.user)}
