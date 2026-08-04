"""
Accounts signals.

- Auto-create Profile when a User is created.
- Record LoginEvent on every successful login.
- Write AuditLog entries for login / logout.
"""
import logging

from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.services import get_client_ip, log_audit_event

logger = logging.getLogger('devlink')


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Ensure every User has a matching Profile."""
    if created:
        from .models import Profile
        Profile.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Record a LoginEvent and write an audit log entry on every successful login."""
    from .models import LoginEvent

    ip = get_client_ip(request) if request else None
    user_agent = (
        request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    )
    session_key = request.session.session_key if request else ''

    LoginEvent.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent,
        session_key=session_key or '',
    )

    log_audit_event(
        event_type='login',
        request=request,
        user=user,
        description=f"Successful login from {ip}",
    )

    logger.info("User %s logged in from %s", user.username, ip)


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Write an audit log entry on logout."""
    if user:
        log_audit_event(
            event_type='logout',
            request=request,
            user=user,
        )


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    """Write an audit log entry on failed login attempts."""
    log_audit_event(
        event_type='login_failed',
        request=request,
        description=f"Failed login for identifier: {credentials.get('username', '?')}",
    )
