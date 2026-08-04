from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Collection(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('owner', 'name')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or f"collection-{self.pk}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.owner.username} / {self.name}"


class CollectionItem(models.Model):
    ITEM_TYPE_CHOICES = [
        ('problem', 'Problem'),
        ('solution', 'Solution'),
    ]
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    object_id = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('collection', 'item_type', 'object_id')
        ordering = ['-added_at']

    def get_item(self):
        if self.item_type == 'problem':
            from problems.models import Problem
            return Problem.objects.filter(pk=self.object_id).first()
        from solutions.models import Solution
        return Solution.objects.filter(pk=self.object_id).first()
