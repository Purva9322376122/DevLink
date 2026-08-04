"""
Accounts services — business logic and mutation functions for the accounts app.

Phase 2 will populate this with email verification, password reset,
login event recording, and session management logic.
"""
from __future__ import annotations


def create_user(username: str, email: str, password: str):
    """
    Create and return a new User + Profile.
    Raises ValueError on duplicate username or email.
    """
    from django.contrib.auth.models import User
    from .models import Profile

    if User.objects.filter(email=email).exists():
        raise ValueError("Email already exists.")
    if User.objects.filter(username=username).exists():
        raise ValueError("Username already exists.")

    user = User.objects.create_user(username=username, email=email, password=password)
    Profile.objects.get_or_create(user=user)
    return user
