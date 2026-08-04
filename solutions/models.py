from django.db import models
from django.contrib.auth.models import User
from problems.models import Problem


class Solution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solutions')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solutions')
    explanation = models.TextField()
    code = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, default='python')
    is_accepted = models.BooleanField(default=False, db_index=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['problem', 'is_accepted', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.problem.title}"


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'solution')

    def __str__(self):
        return f"{self.user.username} voted {self.solution.id}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies'
    )
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.text[:20]}"


class SolutionRevision(models.Model):
    """Snapshot of solution state before each edit."""
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='revisions')
    editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    explanation = models.TextField()
    code = models.TextField(blank=True)
    language = models.CharField(max_length=50, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version']

    def __str__(self):
        return f"Solution #{self.solution_id} v{self.version}"
