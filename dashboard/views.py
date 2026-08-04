import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .selectors import (
    get_dashboard_stats,
    get_profile_completion,
    get_recent_activity,
    get_weekly_contributions,
    get_monthly_contributions,
    get_problems_by_difficulty,
    get_application_statuses,
    get_top_contributors,
)
from notifications.selectors import get_recent_notifications
from solutions.models import Solution
from problems.models import Problem


@login_required
def dashboard_view(request):
    user = request.user
    stats = get_dashboard_stats(user)
    completion = get_profile_completion(user)
    activity = get_recent_activity(user, limit=15)
    recent_notifications = get_recent_notifications(user, limit=5)

    # Recent solutions/problems for the sidebar
    recent_solutions = (
        Solution.objects.filter(user=user)
        .select_related('problem')
        .order_by('-created_at')[:5]
    )
    recent_problems = Problem.objects.filter(user=user).order_by('-created_at')[:5]

    # Chart data — JSON-serialised for template → JS
    weekly = get_weekly_contributions(user)
    monthly = get_monthly_contributions(user)
    difficulty = get_problems_by_difficulty(user)
    app_statuses = get_application_statuses(user)
    top_contributors = get_top_contributors()

    return render(request, 'dashboard/dashboard.html', {
        'stats': stats,
        'completion': completion,
        'activity': activity,
        'recent_notifications': recent_notifications,
        'recent_solutions': recent_solutions,
        'recent_problems': recent_problems,
        'top_contributors': top_contributors,
        # Chart.js data (JSON strings)
        'chart_weekly': json.dumps(weekly),
        'chart_monthly': json.dumps(monthly),
        'chart_difficulty': json.dumps(difficulty),
        'chart_app_statuses': json.dumps(app_statuses),
    })
