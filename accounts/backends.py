"""
Custom authentication backend that allows login with either username or email.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate with username OR email address.

    The standard Django backend only supports username. This backend
    tries username first, then falls back to email lookup.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Try by username first
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Fall back to email
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
