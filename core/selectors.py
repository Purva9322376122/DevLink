"""
Core selectors — shared read-only query helpers.

Selectors never mutate data. Views and services call these instead of
writing raw ORM queries inline.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import User


def get_home_context() -> dict:
    """
    Return the context data required for the homepage.
    Imported lazily to avoid circular imports at startup.
    """
    from django.contrib.auth.models import User as _User
    from django.db.models import Count
    from problems.models import Problem
    from solutions.models import Solution

    return {
        'problems': Problem.objects.order_by('-created_at')[:5],
        'solutions': Solution.objects.order_by('-created_at')[:5],
        'top_users': _User.objects.annotate(
            total_solutions=Count('solutions')
        ).order_by('-total_solutions')[:5],
    }
