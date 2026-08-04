"""
Accounts smoke tests — verify core views return expected status codes.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAuthViews:
    """Login, signup, and logout views."""

    def test_login_page_returns_200(self, client):
        url = reverse('accounts:login')
        response = client.get(url)
        assert response.status_code == 200

    def test_signup_page_returns_200(self, client):
        url = reverse('accounts:signup')
        response = client.get(url)
        assert response.status_code == 200

    def test_logout_redirects(self, auth_client):
        url = reverse('accounts:logout')
        response = auth_client.post(url)
        assert response.status_code in (200, 302)

    def test_signup_creates_user(self, client, db):
        from django.contrib.auth.models import User

        url = reverse('accounts:signup')
        response = client.post(url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
        })
        # Should redirect after successful signup
        assert response.status_code in (200, 302)
        assert User.objects.filter(username='newuser').exists()

    def test_signup_rejects_duplicate_email(self, client, user):
        url = reverse('accounts:signup')
        response = client.post(url, {
            'username': 'anotheruser',
            'email': user.email,   # same email as existing user
            'password': 'SecurePass123!',
        })
        assert response.status_code in (200, 302)
        from django.contrib.auth.models import User
        assert User.objects.filter(username='anotheruser').count() == 0


@pytest.mark.django_db
class TestProfileViews:
    """Profile view requires a real user in the database."""

    def test_own_profile_returns_200(self, auth_client, user):
        url = reverse('accounts:profile', kwargs={'username': user.username})
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_profile_unauthenticated_returns_200(self, client, user):
        """Profiles are publicly visible."""
        url = reverse('accounts:profile', kwargs={'username': user.username})
        response = client.get(url)
        assert response.status_code == 200

    def test_nonexistent_profile_returns_404(self, client, db):
        url = reverse('accounts:profile', kwargs={'username': 'ghost_user_xyz'})
        response = client.get(url)
        assert response.status_code == 404

    def test_edit_profile_requires_login(self, client):
        url = reverse('accounts:edit_profile')
        response = client.get(url)
        assert response.status_code in (302, 301)

    def test_edit_profile_returns_200_for_authenticated(self, auth_client):
        url = reverse('accounts:edit_profile')
        response = auth_client.get(url)
        assert response.status_code == 200
