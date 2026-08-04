"""
Solutions smoke tests.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestSolutionSelectors:

    def test_get_user_top_skills_empty_for_new_user(self, user):
        from accounts.selectors import get_user_top_skills
        skills = get_user_top_skills(user)
        assert skills == []

    def test_get_user_profile_stats_zeros_for_new_user(self, user):
        from accounts.selectors import get_user_profile_stats
        stats = get_user_profile_stats(user)
        assert stats['total_solutions'] == 0
        assert stats['accepted_solutions'] == 0
        assert stats['total_votes'] == 0


@pytest.mark.django_db
class TestToggleVoteService:

    def test_toggle_vote_creates_vote(self, user):
        from problems.models import Problem
        from solutions.models import Solution, Vote
        from solutions.services import toggle_solution_vote

        problem = Problem.objects.create(
            user=user, title='P', description='desc', difficulty='easy'
        )
        solution = Solution.objects.create(
            user=user, problem=problem, explanation='some explanation'
        )
        voted, count = toggle_solution_vote(user, solution)
        assert voted is True
        assert count == 1
        assert Vote.objects.filter(user=user, solution=solution).exists()

    def test_toggle_vote_removes_existing_vote(self, user):
        from problems.models import Problem
        from solutions.models import Solution, Vote
        from solutions.services import toggle_solution_vote

        problem = Problem.objects.create(
            user=user, title='P2', description='desc', difficulty='easy'
        )
        solution = Solution.objects.create(
            user=user, problem=problem, explanation='explanation'
        )
        Vote.objects.create(user=user, solution=solution)

        voted, count = toggle_solution_vote(user, solution)
        assert voted is False
        assert count == 0
        assert not Vote.objects.filter(user=user, solution=solution).exists()


@pytest.mark.django_db
class TestSolutionServices:
    def test_create_solution_revision(self, user):
        from problems.models import Problem
        from solutions.models import Solution, SolutionRevision
        from solutions.services import create_solution_revision
        p = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        s = Solution.objects.create(user=user, problem=p, explanation='exp')
        create_solution_revision(s, user)
        assert SolutionRevision.objects.filter(solution=s, version=1).exists()

    def test_update_solution_creates_revision(self, user):
        from problems.models import Problem
        from solutions.models import Solution, SolutionRevision
        from solutions.services import update_solution
        p = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        s = Solution.objects.create(user=user, problem=p, explanation='old')
        update_solution(s, user, {'explanation': 'new'})
        s.refresh_from_db()
        assert s.explanation == 'new'
        assert SolutionRevision.objects.filter(solution=s).count() == 1

    def test_soft_delete_solution(self, user):
        from problems.models import Problem
        from solutions.models import Solution
        from solutions.services import soft_delete_solution
        p = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        s = Solution.objects.create(user=user, problem=p, explanation='e')
        soft_delete_solution(s, user)
        s.refresh_from_db()
        assert s.is_deleted is True

    def test_edit_comment_updates_text(self, user):
        from problems.models import Problem
        from solutions.models import Solution, Comment
        from solutions.services import edit_comment
        p = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        s = Solution.objects.create(user=user, problem=p, explanation='e')
        c = Comment.objects.create(user=user, solution=s, text='original')
        edit_comment(c, user, 'updated')
        c.refresh_from_db()
        assert c.text == 'updated'
        assert c.is_edited is True

    def test_delete_comment_soft_deletes(self, user):
        from problems.models import Problem
        from solutions.models import Solution, Comment
        from solutions.services import delete_comment
        p = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        s = Solution.objects.create(user=user, problem=p, explanation='e')
        c = Comment.objects.create(user=user, solution=s, text='bye')
        delete_comment(c, user)
        c.refresh_from_db()
        assert c.is_deleted is True

    def test_get_solutions_for_problem_excludes_deleted(self, user):
        from problems.models import Problem
        from solutions.models import Solution
        from solutions.selectors import get_solutions_for_problem
        p = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        Solution.objects.create(user=user, problem=p, explanation='active')
        s2 = Solution.objects.create(user=user, problem=p, explanation='deleted', is_deleted=True)
        results = list(get_solutions_for_problem(p))
        assert s2 not in results


@pytest.mark.django_db
class TestSolutionViews:
    def test_edit_solution_requires_login(self, client, user):
        from problems.models import Problem
        from solutions.models import Solution
        p = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        s = Solution.objects.create(user=user, problem=p, explanation='e')
        url = reverse('edit_solution', kwargs={'solution_id': s.id})
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_solution_history_returns_200(self, client, user):
        from problems.models import Problem
        from solutions.models import Solution
        p = Problem.objects.create(user=user, title='P', description='d', difficulty='easy')
        s = Solution.objects.create(user=user, problem=p, explanation='e')
        url = reverse('solution_history', kwargs={'solution_id': s.id})
        response = client.get(url)
        assert response.status_code == 200
