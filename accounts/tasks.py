"""
Accounts Celery tasks.

All email sending is done asynchronously to avoid blocking web requests.
Tasks retry up to 3 times with exponential backoff on failure.
"""
from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger('devlink')


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3)
def send_activation_email(self, user_id: int) -> None:
    """
    Send an account activation email to a newly registered user.

    The activation link is valid for 24 hours (Django's default for
    PasswordResetTokenGenerator which we reuse here).
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("send_activation_email: user %s not found", user_id)
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    activation_url = (
        f"{settings.SITE_URL}/accounts/activate/{uid}/{token}/"
    )

    subject = render_to_string(
        'accounts/emails/activation_subject.txt',
        {'user': user}
    ).strip()

    body_html = render_to_string(
        'accounts/emails/activation_body.html',
        {'user': user, 'activation_url': activation_url}
    )

    try:
        send_mail(
            subject=subject,
            message=f"Activate your DevLink account: {activation_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=body_html,
            fail_silently=False,
        )
        logger.info("Activation email sent to %s", user.email)
    except Exception as exc:
        logger.warning("Activation email failed for %s: %s", user.email, exc)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, email: str) -> None:
    """
    Send a password reset email.

    Always returns success to the caller regardless of whether the email
    address exists — this prevents email enumeration attacks.
    """
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        # Silently succeed — do not reveal whether the address exists.
        logger.info("Password reset requested for unknown email: %s", email)
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_url = (
        f"{settings.SITE_URL}/accounts/reset-password/{uid}/{token}/"
    )

    subject = render_to_string(
        'accounts/emails/password_reset_subject.txt',
        {'user': user}
    ).strip()

    body_html = render_to_string(
        'accounts/emails/password_reset_body.html',
        {'user': user, 'reset_url': reset_url}
    )

    try:
        send_mail(
            subject=subject,
            message=f"Reset your DevLink password: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=body_html,
            fail_silently=False,
        )
        logger.info("Password reset email sent to %s", email)
    except Exception as exc:
        logger.warning("Password reset email failed for %s: %s", email, exc)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
