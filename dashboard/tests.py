"""
Dashboard tests — selectors, views.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestDashboardSelectors:

    def test_profile_completion_empty_profile(self, user):
        from dashboard.selectors import get_profile_completion
        pct = get_profile_completion(user)
        assert isinstance(pct, int)
        assert 0 <= pct <= 100

    def test_dashboard_stats_zeros_for_new_user(self, user):
        from dashboard.selectors import get_dashboard_stats
        stats = get_dashboard_stats(user)
        assert stats['problems_posted'] == 0
        assert stats['solutions_submitted'] == 0
        assert stats['accepted_solutions'] == 0
        assert stats['connections'] == 0

    def test_get_recent_activity_empty_for_new_user(self, user):
        from dashboard.selectors import get_recent_activity
        activity = get_recent_activity(user)
        assert isinstance(activity, list)
        assert len(activity) == 0

    def test_weekly_contributions_returns_7_days(self, user):
        from dashboard.selectors import get_weekly_contributions
        data = get_weekly_contributions(user)
        assert len(data['labels']) == 7
        assert len(data['problems']) == 7
        assert len(data['solutions']) == 7

    def test_monthly_contributions_returns_12_months(self, user):
        from dashboard.selectors import get_monthly_contributions
        data = get_monthly_contributions(user)
        assert len(data['labels']) == 12

    def test_problems_by_difficulty_structure(self, user):
        from dashboard.selectors import get_problems_by_difficulty
        data = get_problems_by_difficulty(user)
        assert set(data.keys()) == {'easy', 'medium', 'hard'}

    def test_application_statuses_structure(self, user):
        from dashboard.selectors import get_application_statuses
        data = get_application_statuses(user)
        assert set(data.keys()) == {'pending', 'accepted', 'rejected'}

    def test_top_contributors_returns_list(self, db):
        from dashboard.selectors import get_top_contributors
        result = get_top_contributors(limit=5)
        assert isinstance(result, list)

    def test_dashboard_stats_counts_problems(self, user):
        from problems.models import Problem
        from dashboard.selectors import get_dashboard_stats
        Problem.objects.create(user=user, title='T1', description='desc', difficulty='easy')
        Problem.objects.create(user=user, title='T2', description='desc', difficulty='hard')
        stats = get_dashboard_stats(user)
        assert stats['problems_posted'] == 2

    def test_dashboard_stats_counts_solutions(self, user):
        from problems.models import Problem
        from solutions.models import Solution
        from dashboard.selectors import get_dashboard_stats
        problem = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        Solution.objects.create(user=user, problem=problem, explanation='sol')
        stats = get_dashboard_stats(user)
        assert stats['solutions_submitted'] == 1


@pytest.mark.django_db
class TestDashboardViews:

    def test_dashboard_requires_login(self, client):
        url = reverse('dashboard:dashboard')
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_dashboard_returns_200_authenticated(self, auth_client):
        url = reverse('dashboard:dashboard')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_dashboard_contains_username(self, auth_client, user):
        url = reverse('dashboard:dashboard')
        response = auth_client.get(url)
        assert user.username.encode() in response.content
