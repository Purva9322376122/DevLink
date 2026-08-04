from django.db import models
from django.contrib.auth.models import User


class ReputationEvent(models.Model):
    EVENT_TYPES = [
        ('solution_accepted', 'Solution Accepted'),
        ('solution_upvoted', 'Solution Upvoted'),
        ('solution_downvoted', 'Solution Downvoted'),
        ('problem_posted', 'Problem Posted'),
        ('comment_helpful', 'Comment Helpful'),
        ('opportunity_posted', 'Opportunity Posted'),
        ('connection_accepted', 'Connection Accepted'),
        ('upvote_removed', 'Upvote Removed'),
        ('content_deleted', 'Content Deleted'),
        ('spam_reported', 'Spam Reported'),
    ]
    DELTA_MAP = {
        'solution_accepted': 25,
        'solution_upvoted': 10,
        'solution_downvoted': -2,
        'problem_posted': 5,
        'comment_helpful': 2,
        'opportunity_posted': 3,
        'connection_accepted': 5,
        'upvote_removed': -10,
        'content_deleted': -5,
        'spam_reported': -15,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reputation_events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    delta = models.IntegerField()
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f"{self.user.username} {self.event_type} ({self.delta:+d})"


LEVEL_THRESHOLDS = [
    (0, 'Beginner'),
    (100, 'Contributor'),
    (300, 'Intermediate'),
    (700, 'Advanced'),
    (1500, 'Expert'),
    (3000, 'Architect'),
    (6000, 'Legend'),
]


def get_level_for_score(score: int) -> str:
    level = 'Beginner'
    for threshold, name in LEVEL_THRESHOLDS:
        if score >= threshold:
            level = name
    return level


class Badge(models.Model):
    TRIGGER_CHOICES = [
        ('first_problem', 'First Problem'),
        ('first_accepted', 'First Accepted Solution'),
        ('top_contributor', 'Top Contributor'),
        ('mentor', 'Mentor'),
        ('rep_100', '100 Reputation'),
        ('rep_1000', '1000 Reputation'),
        ('connector', '10 Connections'),
    ]
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='bi-award')
    trigger = models.CharField(max_length=30, choices=TRIGGER_CHOICES, unique=True)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f"{self.user.username} — {self.badge.name}"
