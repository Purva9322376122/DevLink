"""
Root conftest.py — shared pytest fixtures for the entire DevLink project.

Usage:
    pytest                    # run all tests
    pytest accounts/          # run accounts tests only
    pytest -m "not slow"      # skip slow tests
    pytest --cov=. --cov-report=html  # with coverage
"""

import logging
import pytest


# ---------------------------------------------------------------------------
# Disable file-based logging during tests to prevent hangs on Windows
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Override logging to console-only during test runs."""
    logging.getLogger().handlers = []
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s %(name)s: %(message)s',
        handlers=[logging.StreamHandler()],
    )


# ---------------------------------------------------------------------------
# Database factories
# ---------------------------------------------------------------------------

@pytest.fixture
def user_factory(db):
    """
    Return a callable that creates User instances with sane defaults.

    Usage:
        def test_something(user_factory):
            user = user_factory(username="alice")
    """
    from django.contrib.auth.models import User

    def make_user(
        username="testuser",
        email="testuser@example.com",
        password="TestPass123!",
        **kwargs,
    ):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs,
        )
        return user

    return make_user


@pytest.fixture
def user(user_factory):
    """A single default authenticated test user."""
    return user_factory()


@pytest.fixture
def profile_factory(db, user_factory):
    """
    Return a callable that creates Profile instances.

    Usage:
        def test_something(profile_factory):
            profile = profile_factory(bio="Hello")
    """
    from accounts.models import Profile

    def make_profile(user=None, **kwargs):
        if user is None:
            user = user_factory()
        profile, _ = Profile.objects.get_or_create(user=user)
        for attr, value in kwargs.items():
            setattr(profile, attr, value)
        if kwargs:
            profile.save()
        return profile

    return make_profile


@pytest.fixture
def auth_client(client, user):
    """A Django test client pre-logged-in as the default test user."""
    client.force_login(user)
    return client


@pytest.fixture
def rf():
    """Django RequestFactory for creating mock requests."""
    from django.test import RequestFactory
    return RequestFactory()


@pytest.fixture
def user_two(user_factory):
    """A second test user for collaboration tests."""
    return user_factory(username="testuser2", email="testuser2@example.com")


@pytest.fixture
def user_three(user_factory):
    """A third test user for multi-user collaboration tests."""
    return user_factory(username="testuser3", email="testuser3@example.com")
