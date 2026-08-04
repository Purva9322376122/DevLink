from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('open_to_work', 'Open to Work'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    skills = models.CharField(max_length=255, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)

    # Phase 4 additions
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    portfolio = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    experience_years = models.PositiveSmallIntegerField(null=True, blank=True)
    availability = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='available',
    )
    timezone = models.CharField(max_length=50, blank=True)
    languages = models.CharField(max_length=255, blank=True)   # comma-separated
    tech_stack = models.CharField(max_length=500, blank=True)  # comma-separated
    interests = models.CharField(max_length=500, blank=True)
    open_to_remote = models.BooleanField(default=False)
    about = models.TextField(blank=True)
    reputation_score = models.IntegerField(default=0, db_index=True)

    def __str__(self):
        return self.user.username


class LoginEvent(models.Model):
    """Records every successful login for audit and session management."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='login_events'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} @ {self.ip_address} ({self.timestamp:%Y-%m-%d %H:%M})"
