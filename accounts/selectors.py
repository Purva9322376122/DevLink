"""
Accounts selectors — read-only query functions for the accounts app.
"""
from __future__ import annotations

from django.contrib.auth.models import User

from solutions.models import Solution
from problems.models import Problem


def get_user_top_skills(user: User) -> list[tuple[str, int]]:
    """
    Return a sorted list of (skill_name, count) tuples derived from the
    tags on problems that the user has submitted solutions for.

    The list is ordered by frequency descending.
    """
    solutions = Solution.objects.filter(user=user).select_related('problem').prefetch_related('problem__tags')
    skill_dict: dict[str, int] = {}
    for sol in solutions:
        for tag in sol.problem.tags.all():
            skill_dict[tag.name] = skill_dict.get(tag.name, 0) + 1
    return sorted(skill_dict.items(), key=lambda x: x[1], reverse=True)


def get_user_profile_stats(user: User) -> dict:
    """
    Return aggregated statistics shown on a user's profile page.

    Keys:
        solutions       — QuerySet of all solutions by the user
        problems        — QuerySet of all problems posted by the user
        total_solutions — int
        accepted_solutions — int
        total_votes     — int (sum of all upvotes across all solutions)
    """
    solutions = Solution.objects.filter(user=user).select_related('problem')
    problems = Problem.objects.filter(user=user)
    total_votes = sum(sol.votes.count() for sol in solutions)
    return {
        'solutions': solutions,
        'problems': problems,
        'total_solutions': solutions.count(),
        'accepted_solutions': solutions.filter(is_accepted=True).count(),
        'total_votes': total_votes,
    }
