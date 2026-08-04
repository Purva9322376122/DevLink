"""
Dashboard selectors — all read-only queries for the dashboard and activity feed.
No mutations allowed here.
"""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone


# ---------------------------------------------------------------------------
# Profile completion
# ---------------------------------------------------------------------------

def get_profile_completion(user: User) -> int:
    """Return a 0-100 integer representing how complete the profile is."""
    try:
        profile = user.profile
    except Exception:
        return 0

    fields = [
        bool(profile.bio),
        bool(profile.skills),
        bool(getattr(profile, 'profile_image', None)),
        bool(profile.github),
        bool(profile.linkedin),
        bool(getattr(profile, 'location', '')),
        bool(getattr(profile, 'portfolio', '')),
    ]
    filled = sum(fields)
    return int((filled / len(fields)) * 100)


# ---------------------------------------------------------------------------
# Core stats
# ---------------------------------------------------------------------------

def get_dashboard_stats(user: User) -> dict:
    """
    Return all numeric statistics shown on the dashboard.
    Uses select_related / prefetch_related to avoid N+1 queries.
    """
    from solutions.models import Solution
    from problems.models import Problem
    from opportunities.models import (
        Application, Opportunity, Connection, Invitation, Message
    )

    solutions_qs = Solution.objects.filter(user=user)
    problems_qs = Problem.objects.filter(user=user)
    apps_sent = Application.objects.filter(user=user)
    apps_received = Application.objects.filter(opportunity__user=user)
    opportunities_qs = Opportunity.objects.filter(user=user)
    connections = Connection.objects.filter(
        Q(user1=user) | Q(user2=user)
    )
    pending_invitations = Invitation.objects.filter(
        receiver=user, status='pending'
    )
    unread_messages = Message.objects.filter(receiver=user, is_read=False)

    from notifications.services import get_unread_count

    return {
        'problems_posted': problems_qs.count(),
        'solutions_submitted': solutions_qs.count(),
        'accepted_solutions': solutions_qs.filter(is_accepted=True).count(),
        'opportunities_posted': opportunities_qs.count(),
        'applications_sent': apps_sent.count(),
        'applications_received': apps_received.count(),
        'connections': connections.count(),
        'pending_invitations': pending_invitations.count(),
        'unread_messages': unread_messages.count(),
        'unread_notifications': get_unread_count(user),
        'followers': 0,   # Phase 3 extension — Follow model added in Phase 3
        'following': 0,
    }


# ---------------------------------------------------------------------------
# Recent activity
# ---------------------------------------------------------------------------

def get_recent_activity(user: User, limit: int = 20) -> list[dict]:
    """
    Return a unified list of recent activity events for the activity feed.
    Each item has: type, actor_username, description, url, timestamp.
    """
    from solutions.models import Solution
    from problems.models import Problem
    from opportunities.models import Application, Opportunity, Connection

    events: list[dict] = []

    # Recent problems
    for p in Problem.objects.filter(user=user).order_by('-created_at')[:5]:
        events.append({
            'type': 'problem_posted',
            'icon': 'bi-question-circle',
            'color': 'primary',
            'description': f'You posted a new problem: <strong>{p.title}</strong>',
            'url': f'/problems/{p.id}/',
            'timestamp': p.created_at,
        })

    # Recent solutions
    for s in Solution.objects.filter(user=user).select_related('problem').order_by('-created_at')[:5]:
        events.append({
            'type': 'solution_submitted',
            'icon': 'bi-lightning-charge',
            'color': 'success',
            'description': f'You submitted a solution to <strong>{s.problem.title}</strong>',
            'url': f'/solutions/problem/{s.problem_id}/',
            'timestamp': s.created_at,
        })

    # Accepted solutions
    for s in Solution.objects.filter(user=user, is_accepted=True).select_related('problem').order_by('-created_at')[:3]:
        events.append({
            'type': 'solution_accepted',
            'icon': 'bi-patch-check',
            'color': 'warning',
            'description': f'Your solution to <strong>{s.problem.title}</strong> was accepted!',
            'url': f'/solutions/problem/{s.problem_id}/',
            'timestamp': s.created_at,
        })

    # Recent connections
    for c in Connection.objects.filter(
        Q(user1=user) | Q(user2=user)
    ).select_related('user1', 'user2').order_by('-created_at')[:5]:
        other = c.user2 if c.user1 == user else c.user1
        events.append({
            'type': 'connection',
            'icon': 'bi-person-check',
            'color': 'info',
            'description': f'You connected with <strong>{other.username}</strong>',
            'url': f'/accounts/profile/{other.username}/',
            'timestamp': c.created_at,
        })

    # Recent applications
    for a in Application.objects.filter(user=user).select_related('opportunity').order_by('-created_at')[:5]:
        events.append({
            'type': 'application_sent',
            'icon': 'bi-send',
            'color': 'secondary',
            'description': f'You applied for <strong>{a.opportunity.title}</strong>',
            'url': '/opportunities/applications/mine/',
            'timestamp': a.created_at,
        })

    # Sort all events by timestamp descending
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    return events[:limit]


# ---------------------------------------------------------------------------
# Chart data
# ---------------------------------------------------------------------------

def get_weekly_contributions(user: User) -> dict:
    """Return contribution counts for the last 7 days (problems + solutions)."""
    from solutions.models import Solution
    from problems.models import Problem

    labels = []
    problem_data = []
    solution_data = []

    today = timezone.now().date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))
        problem_data.append(Problem.objects.filter(user=user, created_at__date=day).count())
        solution_data.append(Solution.objects.filter(user=user, created_at__date=day).count())

    return {'labels': labels, 'problems': problem_data, 'solutions': solution_data}


def get_monthly_contributions(user: User) -> dict:
    """Return contribution counts for the last 12 months."""
    from solutions.models import Solution
    from problems.models import Problem

    labels = []
    problem_data = []
    solution_data = []

    today = timezone.now().date()
    for i in range(11, -1, -1):
        # First day of each month
        month_date = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        labels.append(month_date.strftime('%b'))
        problem_data.append(
            Problem.objects.filter(
                user=user,
                created_at__year=month_date.year,
                created_at__month=month_date.month,
            ).count()
        )
        solution_data.append(
            Solution.objects.filter(
                user=user,
                created_at__year=month_date.year,
                created_at__month=month_date.month,
            ).count()
        )

    return {'labels': labels, 'problems': problem_data, 'solutions': solution_data}


def get_problems_by_difficulty(user: User) -> dict:
    """Count problems posted per difficulty level."""
    from problems.models import Problem
    counts = (
        Problem.objects.filter(user=user)
        .values('difficulty')
        .annotate(count=Count('id'))
    )
    result = {'easy': 0, 'medium': 0, 'hard': 0}
    for row in counts:
        result[row['difficulty']] = row['count']
    return result


def get_application_statuses(user: User) -> dict:
    """Count user's applications by status."""
    from opportunities.models import Application
    counts = (
        Application.objects.filter(user=user)
        .values('status')
        .annotate(count=Count('id'))
    )
    result = {'pending': 0, 'accepted': 0, 'rejected': 0}
    for row in counts:
        result[row['status']] = row['count']
    return result


# ---------------------------------------------------------------------------
# Top contributors leaderboard
# ---------------------------------------------------------------------------

def get_top_contributors(limit: int = 5) -> list:
    """Return the top N users by accepted solution count."""
    from solutions.models import Solution
    from django.contrib.auth.models import User as _User
    return list(
        _User.objects.annotate(
            accepted=Count('solutions', filter=Q(solutions__is_accepted=True))
        ).order_by('-accepted').values('username', 'accepted')[:limit]
    )
