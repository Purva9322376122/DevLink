"""
Problems selectors — read-only query functions.
No mutations allowed here.
"""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from .models import Problem, Tag


# ---------------------------------------------------------------------------
# Problems
# ---------------------------------------------------------------------------

def get_problems(
    query: str | None = None,
    tag: str | None = None,
    difficulty: str | None = None,
    language: str | None = None,
    category: str | None = None,
    ordering: str = '-created_at',
) -> QuerySet:
    """Filtered, ordered QuerySet of active problems."""
    qs = (
        Problem.objects.filter(is_deleted=False)
        .select_related('user')
        .prefetch_related('tags')
    )
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if tag:
        qs = qs.filter(tags__name__iexact=tag)
    if difficulty:
        qs = qs.filter(difficulty=difficulty)
    if language:
        qs = qs.filter(language__iexact=language)
    if category:
        qs = qs.filter(category__iexact=category)
    return qs.order_by(ordering)


def get_popular_problems(limit: int = 10) -> QuerySet:
    """Problems ordered by view count descending."""
    return (
        Problem.objects.filter(is_deleted=False)
        .select_related('user')
        .order_by('-view_count')[:limit]
    )


def get_trending_problems(limit: int = 10) -> QuerySet:
    """Problems from the last 7 days with most solutions."""
    week_ago = timezone.now() - timedelta(days=7)
    return (
        Problem.objects.filter(is_deleted=False, created_at__gte=week_ago)
        .annotate(solution_count=Count('solutions'))
        .select_related('user')
        .order_by('-solution_count', '-view_count')[:limit]
    )


def get_related_problems(problem, limit: int = 5) -> QuerySet:
    """Problems sharing at least one tag with *problem*."""
    tag_ids = problem.tags.values_list('id', flat=True)
    return (
        Problem.objects.filter(tags__in=tag_ids, is_deleted=False)
        .exclude(id=problem.id)
        .distinct()
        .select_related('user')
        .order_by('-view_count')[:limit]
    )


def get_problem_revision_history(problem) -> QuerySet:
    """All revisions for a problem, newest first."""
    from .models import ProblemRevision
    return ProblemRevision.objects.filter(problem=problem).select_related('editor')


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

def get_popular_tags(limit: int = 20) -> QuerySet:
    return Tag.objects.order_by('-usage_count')[:limit]


def get_tag_suggestions(query: str, limit: int = 10) -> QuerySet:
    return Tag.objects.filter(name__icontains=query).order_by('-usage_count')[:limit]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def get_unresolved_reports(limit: int = 50) -> QuerySet:
    from .models import Report
    return Report.objects.filter(is_resolved=False).select_related('reporter')
