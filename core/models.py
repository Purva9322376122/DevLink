from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    """Records security-sensitive actions for auditing purposes."""

    EVENT_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('login_failed', 'Login Failed'),
        ('account_activated', 'Account Activated'),
        ('password_reset', 'Password Reset'),
        ('account_deactivated', 'Account Deactivated'),
        ('content_deleted', 'Content Deleted'),
        ('permission_denied', 'Permission Denied'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]

    def __str__(self):
        return f"[{self.event_type}] {self.user} @ {self.timestamp}"
