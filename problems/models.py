from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    usage_count = models.PositiveIntegerField(default=0, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or self.name.lower().replace(' ', '-')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='problems')
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default='easy', db_index=True
    )
    tags = models.ManyToManyField(Tag, blank=True)
    # Phase 5 additions
    language = models.CharField(max_length=50, blank=True, db_index=True)
    category = models.CharField(max_length=100, blank=True, db_index=True)
    view_count = models.PositiveIntegerField(default=0, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['difficulty', 'created_at']),
            models.Index(fields=['is_deleted', '-created_at']),
        ]

    def __str__(self):
        return self.title


class ProblemView(models.Model):
    """Tracks unique views per user/IP per day."""
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='problem_views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['problem', 'viewed_at']),
        ]


class ProblemRevision(models.Model):
    """Snapshot of problem state before each edit."""
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='revisions')
    editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    difficulty = models.CharField(max_length=10)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version']

    def __str__(self):
        return f"Problem #{self.problem_id} v{self.version}"


class Report(models.Model):
    """Content report submitted by a user."""
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('offensive', 'Offensive'),
        ('duplicate', 'Duplicate'),
        ('incorrect', 'Incorrect Information'),
        ('other', 'Other'),
    ]
    CONTENT_TYPE_CHOICES = [
        ('problem', 'Problem'),
        ('solution', 'Solution'),
        ('comment', 'Comment'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_filed')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, db_index=True)
    object_id = models.PositiveIntegerField()
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('reporter', 'content_type', 'object_id')

    def __str__(self):
        return f"Report by {self.reporter.username} on {self.content_type}:{self.object_id}"
