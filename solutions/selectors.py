"""
Solutions selectors — read-only query helpers.
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import Count, QuerySet


def get_solutions_for_problem(problem, sort: str = 'latest') -> QuerySet:
    """Return active solutions for a problem."""
    qs = problem.solutions.filter(is_deleted=False).select_related('user')
    if sort == 'popular':
        return qs.annotate(
            vote_count=Count('votes')
        ).order_by('-is_accepted', '-vote_count', '-created_at')
    return qs.order_by('-is_accepted', '-created_at')


def get_user_voted_solution_ids(user: User, solutions) -> list[int]:
    """Return list of solution IDs the user has voted on."""
    from .models import Vote
    return list(
        Vote.objects.filter(user=user, solution__in=solutions)
        .values_list('solution_id', flat=True)
    )


def get_solution_comments(solution) -> QuerySet:
    """Return top-level, non-deleted comments with replies prefetched."""
    from .models import Comment
    return (
        solution.comments.filter(parent=None, is_deleted=False)
        .select_related('user')
        .prefetch_related('replies__user')
    )


def get_solution_revision_history(solution) -> QuerySet:
    """All revisions for a solution, newest first."""
    from .models import SolutionRevision
    return SolutionRevision.objects.filter(solution=solution).select_related('editor')
