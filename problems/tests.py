"""
Problems smoke tests.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestProblemListView:

    def test_problem_list_returns_200(self, client):
        url = reverse('problem_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_problem_list_with_search_query(self, client):
        url = reverse('problem_list')
        response = client.get(url, {'q': 'python'})
        assert response.status_code == 200

    def test_problem_list_with_tag_filter(self, client):
        url = reverse('problem_list')
        response = client.get(url, {'tag': 'django'})
        assert response.status_code == 200

    def test_problem_list_with_difficulty_filter(self, client):
        url = reverse('problem_list')
        response = client.get(url, {'difficulty': 'easy'})
        assert response.status_code == 200


@pytest.mark.django_db
class TestProblemDetailView:

    def test_problem_detail_returns_404_for_nonexistent(self, client, db):
        url = reverse('problem_detail', kwargs={'problem_id': 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_problem_detail_returns_200_for_existing(self, client, user):
        from problems.models import Problem
        problem = Problem.objects.create(
            user=user,
            title='Test Problem',
            description='This is a test problem description.',
            difficulty='easy',
        )
        url = reverse('problem_detail', kwargs={'problem_id': problem.id})
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestCreateProblemView:

    def test_create_problem_requires_login(self, client, db):
        url = reverse('create_problem')
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_create_problem_returns_200_for_authenticated(self, auth_client):
        url = reverse('create_problem')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_create_problem_post_creates_record(self, auth_client, user):
        from problems.models import Problem
        url = reverse('create_problem')
        response = auth_client.post(url, {
            'title': 'My Test Problem',
            'description': 'A detailed description of the problem.',
            'difficulty': 'medium',
            'tags': 'python, django',
        })
        assert response.status_code in (200, 302)
        assert Problem.objects.filter(title='My Test Problem', user=user).exists()


@pytest.mark.django_db
class TestProblemServices:
    def test_record_problem_view_increments_count(self, user, rf):
        from problems.models import Problem
        from problems.services import record_problem_view
        problem = Problem.objects.create(user=user, title='VP', description='d', difficulty='easy')
        request = rf.get('/')
        request.user = user
        record_problem_view(problem, request)
        problem.refresh_from_db()
        assert problem.view_count == 1

    def test_record_problem_view_unique_per_day(self, user, rf):
        from problems.models import Problem
        from problems.services import record_problem_view
        problem = Problem.objects.create(user=user, title='VP2', description='d', difficulty='easy')
        request = rf.get('/')
        request.user = user
        record_problem_view(problem, request)
        record_problem_view(problem, request)  # duplicate
        problem.refresh_from_db()
        assert problem.view_count == 1

    def test_create_problem_revision(self, user):
        from problems.models import Problem, ProblemRevision
        from problems.services import create_problem_revision
        problem = Problem.objects.create(user=user, title='T', description='d', difficulty='easy')
        create_problem_revision(problem, user)
        assert ProblemRevision.objects.filter(problem=problem, version=1).exists()

    def test_update_problem_creates_revision(self, user):
        from problems.models import Problem, ProblemRevision
        from problems.services import update_problem
        problem = Problem.objects.create(user=user, title='T', description='d', difficulty='easy')
        update_problem(problem, user, {'title': 'Updated Title'})
        assert ProblemRevision.objects.filter(problem=problem).count() == 1
        problem.refresh_from_db()
        assert problem.title == 'Updated Title'

    def test_soft_delete_problem(self, user):
        from problems.models import Problem
        from problems.services import soft_delete_problem
        problem = Problem.objects.create(user=user, title='T', description='d', difficulty='easy')
        soft_delete_problem(problem, user)
        problem.refresh_from_db()
        assert problem.is_deleted is True

    def test_soft_delete_permission_error(self, user, user_factory):
        from problems.models import Problem
        from problems.services import soft_delete_problem
        other = user_factory(username='other2', email='o2@x.com')
        problem = Problem.objects.create(user=user, title='T', description='d', difficulty='easy')
        with pytest.raises(PermissionError):
            soft_delete_problem(problem, other)

    def test_submit_report(self, user):
        from problems.models import Report
        from problems.services import submit_report
        submit_report(user, 'problem', 1, 'spam', 'test')
        assert Report.objects.filter(reporter=user, reason='spam').exists()

    def test_get_popular_problems(self, user):
        from problems.models import Problem
        from problems.selectors import get_popular_problems
        Problem.objects.create(user=user, title='P1', description='d', difficulty='easy', view_count=10)
        Problem.objects.create(user=user, title='P2', description='d', difficulty='easy', view_count=5)
        results = get_popular_problems(limit=5)
        assert list(results)[0].view_count >= list(results)[1].view_count

    def test_get_related_problems(self, user):
        from problems.models import Problem, Tag
        from problems.selectors import get_related_problems
        tag = Tag.objects.create(name='testrelatedd')
        p1 = Problem.objects.create(user=user, title='P1', description='d', difficulty='easy')
        p2 = Problem.objects.create(user=user, title='P2', description='d', difficulty='easy')
        p1.tags.add(tag)
        p2.tags.add(tag)
        related = list(get_related_problems(p1))
        assert p2 in related

    def test_get_tag_suggestions(self, user):
        from problems.models import Tag
        from problems.selectors import get_tag_suggestions
        Tag.objects.create(name='djangoframework')
        results = get_tag_suggestions('djangoframe')
        assert results.count() >= 1


@pytest.mark.django_db
class TestMarkdownRendering:
    def test_render_markdown_basic(self):
        from solutions.services import render_markdown
        html = render_markdown('**bold**')
        assert '<strong>bold</strong>' in html

    def test_render_markdown_sanitizes_script(self):
        from solutions.services import render_markdown
        html = render_markdown('<script>alert("xss")</script>')
        assert '<script>' not in html

    def test_render_markdown_code_block(self):
        from solutions.services import render_markdown
        html = render_markdown('```python\nprint("hi")\n```')
        assert 'print' in html

    def test_render_markdown_table(self):
        from solutions.services import render_markdown
        md = '| A | B |\n|---|---|\n| 1 | 2 |'
        html = render_markdown(md)
        assert '<table' in html

    def test_render_markdown_link(self):
        from solutions.services import render_markdown
        html = render_markdown('[Click](https://example.com)')
        assert 'href' in html

    def test_render_markdown_strips_onclick(self):
        from solutions.services import render_markdown
        html = render_markdown('<a onclick="evil()">x</a>')
        assert 'onclick' not in html


@pytest.mark.django_db
class TestProblemViews:
    def test_edit_problem_requires_login(self, client, user):
        from problems.models import Problem
        p = Problem.objects.create(user=user, title='T', description='d', difficulty='easy')
        url = reverse('edit_problem', kwargs={'problem_id': p.id})
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_edit_problem_owner_gets_200(self, auth_client, user):
        from problems.models import Problem
        p = Problem.objects.create(user=user, title='T', description='d', difficulty='easy')
        url = reverse('edit_problem', kwargs={'problem_id': p.id})
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_problem_history_returns_200(self, client, user):
        from problems.models import Problem
        p = Problem.objects.create(user=user, title='T', description='d', difficulty='easy')
        url = reverse('problem_history', kwargs={'problem_id': p.id})
        response = client.get(url)
        assert response.status_code == 200

    def test_tag_list_returns_200(self, client, db):
        url = reverse('tag_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_tag_autocomplete_returns_json(self, client, db):
        url = reverse('tag_autocomplete')
        response = client.get(url, {'q': 'py'})
        assert response.status_code == 200
        data = response.json()
        assert 'tags' in data
