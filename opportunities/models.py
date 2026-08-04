from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Opportunity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opportunities')

    title = models.CharField(max_length=255)
    description = models.TextField()

    required_skills = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Opportunities"

class Invitation(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invites')

    message = models.TextField(blank=True)

    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"
    
    

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    message = models.TextField()
    github = models.URLField(blank=True, null=True)
    resume = models.URLField(blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # ⭐ NEW

    created_at = models.DateTimeField(auto_now_add=True)




class Connection(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="connections_sent")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="connections_received")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user1} ↔ {self.user2}"
    
# class Message(models.Model):
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
#     receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
#     content = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('file', 'File'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    is_delivered = models.BooleanField(default=False)
    
    # File sharing support
    file_url = models.URLField(blank=True, null=True)
    file_type = models.CharField(
        max_length=10, 
        choices=FILE_TYPE_CHOICES, 
        blank=True,
        null=True
    )
    
    # Message pinning
    is_pinned = models.BooleanField(default=False, db_index=True)
    
    # Edit tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sender', 'receiver', '-timestamp']),
            models.Index(fields=['receiver', 'is_read', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver}"
    
    def mark_delivered(self):
        """Mark message as delivered to recipient."""
        if not self.is_delivered:
            self.is_delivered = True
            self.save(update_fields=['is_delivered'])
    
    def mark_read(self):
        """Mark message as read by recipient."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])