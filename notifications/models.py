from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """A single in-app notification delivered to a user."""

    VERB_CHOICES = [
        ('connection_request', 'Connection Request'),
        ('connection_accepted', 'Connection Accepted'),
        ('new_message', 'New Message'),
        ('solution_commented', 'Solution Commented'),
        ('comment_replied', 'Comment Replied'),
        ('solution_accepted', 'Solution Accepted'),
        ('solution_upvoted', 'Solution Upvoted'),
        ('application_received', 'Opportunity Application'),
        ('application_accepted', 'Application Accepted'),
        ('application_rejected', 'Application Rejected'),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='notifications', db_index=True
    )
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='acted_notifications'
    )
    verb = models.CharField(max_length=30, choices=VERB_CHOICES, db_index=True)

    # Generic FK — the resource this notification points to
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type', 'object_id')

    # Pre-resolved URL to avoid template-side URL lookups
    target_url = models.CharField(max_length=500, blank=True)
    # Short human-readable summary
    preview = models.CharField(max_length=200, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.verb}] → {self.recipient.username}"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
