"""
Tests for the bookmarks app.
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from bookmarks.models import Bookmark
from bookmarks.services import toggle_bookmark, is_bookmarked, get_user_bookmarks
from problems.models import Problem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return User.objects.create_user(username='bookmarker', password='pass123', email='bm@test.com')


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username='other', password='pass123', email='other@test.com')


@pytest.fixture
def problem(db, other_user):
    return Problem.objects.create(
        user=other_user,
        title='Test Problem',
        description='A test problem description',
    )


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestToggleBookmark:
    def test_toggle_creates_bookmark(self, user, problem):
        bookmarked, total = toggle_bookmark(user, problem)
        assert bookmarked is True
        assert total == 1
        assert Bookmark.objects.filter(user=user).count() == 1

    def test_toggle_removes_on_second_call(self, user, problem):
        toggle_bookmark(user, problem)
        bookmarked, total = toggle_bookmark(user, problem)
        assert bookmarked is False
        assert total == 0
        assert Bookmark.objects.filter(user=user).count() == 0

    def test_toggle_is_idempotent_create_destroy(self, user, problem):
        toggle_bookmark(user, problem)
        toggle_bookmark(user, problem)
        toggle_bookmark(user, problem)
        # Third toggle should re-create it
        assert Bookmark.objects.filter(user=user).exists()

    def test_total_count_across_users(self, user, other_user, problem):
        toggle_bookmark(user, problem)
        toggle_bookmark(other_user, problem)
        _, total = toggle_bookmark(user, problem)  # user removes
        # other_user still has it
        assert total == 1


@pytest.mark.django_db
class TestIsBookmarked:
    def test_returns_false_for_non_bookmarked(self, user, problem):
        assert is_bookmarked(user, problem) is False

    def test_returns_true_after_bookmark(self, user, problem):
        toggle_bookmark(user, problem)
        assert is_bookmarked(user, problem) is True

    def test_returns_false_after_unbookmark(self, user, problem):
        toggle_bookmark(user, problem)
        toggle_bookmark(user, problem)
        assert is_bookmarked(user, problem) is False

    def test_anonymous_user_returns_false(self, problem):
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        assert is_bookmarked(anon, problem) is False


@pytest.mark.django_db
class TestGetUserBookmarks:
    def test_returns_empty_queryset(self, user):
        result = get_user_bookmarks(user)
        assert result.count() == 0

    def test_returns_user_bookmarks(self, user, problem):
        toggle_bookmark(user, problem)
        result = get_user_bookmarks(user)
        assert result.count() == 1


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBookmarkListView:
    def test_requires_login(self):
        client = Client()
        url = reverse('bookmarks:list')
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_returns_200_for_authenticated(self, user):
        client = Client()
        client.login(username='bookmarker', password='pass123')
        url = reverse('bookmarks:list')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestToggleBookmarkView:
    def test_requires_login(self, problem):
        from django.contrib.contenttypes.models import ContentType
        client = Client()
        ct = ContentType.objects.get_for_model(Problem)
        url = reverse('bookmarks:toggle', args=[ct.id, problem.pk])
        response = client.post(url)
        assert response.status_code == 302

    def test_returns_json_on_success(self, user, problem):
        from django.contrib.contenttypes.models import ContentType
        client = Client()
        client.login(username='bookmarker', password='pass123')
        ct = ContentType.objects.get_for_model(Problem)
        url = reverse('bookmarks:toggle', args=[ct.id, problem.pk])
        response = client.post(url, content_type='application/json')
        assert response.status_code == 200
        data = response.json()
        assert 'bookmarked' in data
        assert 'total' in data
        assert data['bookmarked'] is True

    def test_toggle_removes_bookmark_via_view(self, user, problem):
        from django.contrib.contenttypes.models import ContentType
        client = Client()
        client.login(username='bookmarker', password='pass123')
        ct = ContentType.objects.get_for_model(Problem)
        url = reverse('bookmarks:toggle', args=[ct.id, problem.pk])
        # First toggle — create
        client.post(url, content_type='application/json')
        # Second toggle — remove
        response = client.post(url, content_type='application/json')
        data = response.json()
        assert data['bookmarked'] is False

    def test_get_method_not_allowed(self, user, problem):
        from django.contrib.contenttypes.models import ContentType
        client = Client()
        client.login(username='bookmarker', password='pass123')
        ct = ContentType.objects.get_for_model(Problem)
        url = reverse('bookmarks:toggle', args=[ct.id, problem.pk])
        response = client.get(url)
        assert response.status_code == 405
