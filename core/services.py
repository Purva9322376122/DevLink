"""
Core services — shared utilities and base service helpers.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest


def get_client_ip(request: "HttpRequest") -> str:
    """Extract the real client IP address from a request object."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def log_audit_event(
    event_type: str,
    request: "HttpRequest | None" = None,
    user=None,
    resource_type: str = '',
    resource_id: str = '',
    description: str = '',
) -> None:
    """
    Create an AuditLog entry.

    Importing AuditLog here (not at module level) avoids circular import
    issues during Django startup.
    """
    from core.models import AuditLog

    resolved_user = user
    if resolved_user is None and request is not None:
        resolved_user = request.user if request.user.is_authenticated else None

    AuditLog.objects.create(
        user=resolved_user,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id),
        ip_address=get_client_ip(request) if request else None,
        user_agent=(
            request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
        ),
        description=description,
    )
