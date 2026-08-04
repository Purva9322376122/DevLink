# Implementation Plan: DevLink v1.0

## Overview

Incremental implementation plan for transforming the existing Connect Django project into the DevLink v1.0 production-ready developer networking platform. Tasks are organized across 12 phases, building on each other from infrastructure through to final UI polish. Each task references the specific requirements it satisfies.

---

## Tasks

## Phase 1 — Foundation & Infrastructure

- [-] 1. Audit and clean dead code
  - [x] 1.1 Remove duplicate `applications` URL name in `Connect/opportunities/urls.py` — rename the second one to `my_applications` and update the view reference
  - [x] 1.2 Remove unused `login_view` function from `Connect/accounts/views.py` (Django built-in LoginView is used instead)
  - [x] 1.3 Remove all commented-out code blocks from `Connect/accounts/views.py`, `Connect/opportunities/views.py`, `Connect/solutions/views.py`, `Connect/Connect/views.py`, `Connect/problems/views.py`
  - [x] 1.4 Fix syntax error in `Connect/opportunities/routing.py` (malformed regex string)
  - [x] 1.5 Remove duplicate `MEDIA_URL` and `MEDIA_ROOT` definitions in `Connect/Connect/settings.py`
  - [ ] 1.6 Delete empty `Connect/static/css/style.css` and replace with `Connect/static/css/devlink.css` placeholder

- [-] 2. Create `core` app
  - [ ] 2.1 Run `python manage.py startapp core` inside `Connect/` directory (or manually create the directory structure)
  - [x] 2.2 Create `Connect/core/services.py` with base service class and `get_client_ip` utility
  - [x] 2.3 Create `Connect/core/selectors.py` with base selector utilities
  - [x] 2.4 Create `Connect/core/permissions.py` with `IsOwnerOrReadOnly`, `IsOwner`, `IsConnected`, `IsPublic` DRF permission classes
  - [ ] 2.5 Create `Connect/core/validators.py` with `FileValidator` class (MIME check, size limit, filename sanitization)
  - [ ] 2.6 Create `Connect/core/middleware.py` with `SecurityHeadersMiddleware` skeleton
  - [ ] 2.7 Create `Connect/core/exceptions.py` with `custom_exception_handler` for DRF
  - [ ] 2.8 Create `Connect/core/pagination.py` with `DevLinkPagination` class (page_size=20, max=100)
  - [ ] 2.9 Add `core.apps.CoreConfig` to `INSTALLED_APPS` in settings

- [-] 3. Refactor business logic into services/selectors
  - [x] 3.1 Create `Connect/accounts/selectors.py` — move profile stats calculation (skill_dict loop) out of `accounts/views.py:profile_view` into `get_user_top_skills(user)` selector
  - [ ] 3.2 Create `Connect/accounts/services.py` — skeleton for future auth services
  - [x] 3.3 Create `Connect/opportunities/selectors.py` — move conversation aggregation loop out of `opportunities/views.py:messages_list` into `get_conversations(user)` selector
  - [ ] 3.4 Create `Connect/solutions/services.py` — move vote toggle logic out of `solutions/views.py:toggle_vote` into `toggle_solution_vote(user, solution)` service
  - [ ] 3.5 Create `Connect/problems/selectors.py` — move filtered problem queryset logic into `get_problems(query, tag, difficulty)` selector
  - [ ] 3.6 Update views to call selectors/services instead of containing the logic directly

- [-] 4. Split settings into base/development/production
  - [ ] 4.1 Create `Connect/Connect/settings/` directory
  - [ ] 4.2 Create `Connect/Connect/settings/__init__.py` (empty)
  - [ ] 4.3 Create `Connect/Connect/settings/base.py` — migrate all shared settings from `settings.py` (INSTALLED_APPS, MIDDLEWARE, TEMPLATES, AUTH_PASSWORD_VALIDATORS, I18N, STATIC, MEDIA, LOGIN_URL, ASGI_APPLICATION, CHANNEL_LAYERS)
  - [ ] 4.4 Create `Connect/Connect/settings/development.py` — DEBUG=True, SQLite database, InMemoryChannelLayer, EMAIL_BACKEND console, extend base.py
  - [ ] 4.5 Create `Connect/Connect/settings/production.py` — DEBUG=False, PostgreSQL via DATABASE_URL, Redis channel layer, secure cookie settings, HSTS, extend base.py
  - [ ] 4.6 Update `Connect/manage.py` default `DJANGO_SETTINGS_MODULE` to `Connect.settings.development`
  - [ ] 4.7 Update `Connect/Connect/wsgi.py` default `DJANGO_SETTINGS_MODULE` to `Connect.settings.production`
  - [ ] 4.8 Update `Connect/Connect/asgi.py` default `DJANGO_SETTINGS_MODULE` to `Connect.settings.production`
  - [ ] 4.9 Delete old `Connect/Connect/settings.py`

- [-] 5. Add .env configuration
  - [ ] 5.1 Add `django-environ==0.11.2` to `requirements/base.txt`
  - [ ] 5.2 Update `Connect/Connect/settings/base.py` to use `environ.Env()` for SECRET_KEY and ALLOWED_HOSTS
  - [ ] 5.3 Create `Connect/.env` with development defaults (SECRET_KEY, DEBUG=True, ALLOWED_HOSTS=localhost)
  - [ ] 5.4 Create `Connect/.env.example` documenting all required variables (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL, REDIS_URL, EMAIL_HOST, etc.)
  - [ ] 5.5 Add `Connect/.env` to `.gitignore`

- [ ] 6. Configure logging
  - [ ] 6.1 Add `LOGGING` dict to `Connect/Connect/settings/base.py` with console handler (DEBUG level) and file handler writing to `logs/devlink.log`
  - [ ] 6.2 Create `Connect/logs/` directory with `.gitkeep`
  - [ ] 6.3 Add `logs/` to `.gitignore`

- [ ] 7. Configure Redis channel layer for production
  - [ ] 7.1 Add `channels-redis==4.2.0` to `requirements/production.txt`
  - [ ] 7.2 Update `Connect/Connect/settings/production.py` CHANNEL_LAYERS to use `channels_redis.core.RedisChannelLayer` with `REDIS_URL` env var
  - [ ] 7.3 Add `REDIS_URL` to `.env.example`

- [ ] 8. Configure Celery
  - [ ] 8.1 Add `celery==5.3.6` and `redis==5.0.1` to `requirements/base.txt`
  - [ ] 8.2 Create `Connect/Connect/celery.py` with Celery app instance, `autodiscover_tasks`, and Beat schedule skeleton
  - [ ] 8.3 Update `Connect/Connect/__init__.py` to import Celery app (`from .celery import app as celery_app`)
  - [ ] 8.4 Add Celery settings block to `Connect/Connect/settings/base.py` (CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CELERY_TASK_SERIALIZER, etc.)
  - [ ] 8.5 Add `django-celery-beat==2.6.0` to `requirements/production.txt`

- [-] 9. Configure Docker and deployment files
  - [x] 9.1 Create `Connect/requirements/base.txt` with all current dependencies pinned
  - [x] 9.2 Create `Connect/requirements/development.txt` extending base with dev-only packages
  - [x] 9.3 Create `Connect/requirements/production.txt` extending base with prod packages (gunicorn, psycopg2-binary, channels-redis, celery, daphne)
  - [x] 9.4 Create `Connect/Dockerfile` with multi-stage build (builder + production stages)
  - [x] 9.5 Create `Connect/docker-compose.yml` with services: postgres, redis, web, daphne, celery_worker, celery_beat, nginx
  - [x] 9.6 Create `Connect/docker/nginx.conf` with static/media serving and WebSocket proxy to Daphne
  - [x] 9.7 Create `Connect/docker/entrypoint.sh` (migrate + collectstatic + gunicorn)
  - [x] 9.8 Create `Connect/.dockerignore`

- [ ] 10. Add pytest and test setup
  - [x] 10.1 Add `pytest==8.3.4`, `pytest-django==4.8.0`, `factory-boy==3.3.1` to `requirements/development.txt`
  - [x] 10.2 Create `Connect/pytest.ini` with `DJANGO_SETTINGS_MODULE = Connect.settings.development` and `testpaths = .`
  - [x] 10.3 Create `Connect/conftest.py` with `UserFactory`, `ProfileFactory` fixtures
  - [x] 10.4 Write smoke tests in `Connect/accounts/tests.py` — test signup view returns 200, login view returns 200, profile view returns 200 for existing user
  - [x] 10.5 Write smoke tests in `Connect/problems/tests.py` — test problem list returns 200, problem detail returns 200
  - [x] 10.6 Write smoke tests in `Connect/opportunities/tests.py` — test opportunity list returns 200
  - [x] 10.7 Verify all smoke tests pass with `pytest`

- [-] 11. Checkpoint — Phase 1 complete
  - Ensure all smoke tests pass, settings split is working, and `python manage.py check` reports no errors. Ask the user if questions arise.


## Phase 2 — Auth Hardening

- [ ] 12. Implement email verification flow
  - [ ] 12.1 Modify `signup_view` in `Connect/accounts/views.py` to set `is_active=False` on new users and redirect to a "check your email" page instead of auto-login
  - [ ] 12.2 Create `Connect/accounts/tasks.py` with `send_activation_email(user_id)` Celery task — generate signed activation token via `django.core.signing`, build absolute URL, send via `send_mail`
  - [ ] 12.3 Implement `activate_account` view — verify token with `TimestampSigner`, set `is_active=True`, redirect to login with success message; handle expired/invalid tokens with error page and resend link
  - [ ] 12.4 Create activation email templates: `Connect/accounts/templates/emails/activation_subject.txt` and `activation_body.html`
  - [ ] 12.5 Wire activation URL in `Connect/accounts/urls.py`
  - _Requirements: 1.1, 1.5, 1.6_

- [ ] 13. Implement password reset flow
  - [ ] 13.1 Create `send_password_reset_email(email)` Celery task in `Connect/accounts/tasks.py` — always sends response regardless of email existence (prevents enumeration per Requirement 3.1)
  - [ ] 13.2 Implement `forgot_password_view` and `reset_password_confirm_view` in `accounts/views.py` using Django's `PasswordResetForm` / `SetPasswordForm`
  - [ ] 13.3 Create password reset templates: `password_reset.html`, `password_reset_confirm.html`, `password_reset_email.html`
  - [ ] 13.4 Wire password reset URLs in `accounts/urls.py`
  - [ ] 13.5 Add post-reset signal handler to invalidate all active sessions for the user (`flush_sessions`)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 14. Add JWT authentication
  - [ ] 14.1 Add `djangorestframework-simplejwt==5.3.1` to `requirements/base.txt`
  - [ ] 14.2 Add `SIMPLE_JWT` settings block to `Connect/Connect/settings/base.py` (ACCESS_TOKEN_LIFETIME=60min, REFRESH_TOKEN_LIFETIME=7d, ROTATE_REFRESH_TOKENS=True, BLACKLIST_AFTER_ROTATION=True)
  - [ ] 14.3 Add `rest_framework_simplejwt.token_blacklist` to `INSTALLED_APPS` and run migration
  - [ ] 14.4 Wire `/api/auth/token/` and `/api/auth/token/refresh/` in `Connect/Connect/urls.py`
  - [ ] 14.5 Set `DEFAULT_AUTHENTICATION_CLASSES` in DRF settings to include both `JWTAuthentication` and `SessionAuthentication`
  - _Requirements: 2.2, 2.3, 2.5_

- [ ] 15. Add custom auth backend (email or username login)
  - [ ] 15.1 Create `Connect/accounts/backends.py` with `EmailOrUsernameBackend` — attempts lookup by username then by email
  - [ ] 15.2 Add backend to `AUTHENTICATION_BACKENDS` in `settings/base.py`
  - [ ] 15.3 Update login form to label the identifier field "Username or Email"
  - _Requirements: 2.1, 2.10_

- [ ] 16. Implement login event recording and rate limiting
  - [ ] 16.1 Create `LoginEvent` model in `Connect/accounts/models.py` with fields: user, ip_address, user_agent, session_key, timestamp; create and run migration
  - [ ] 16.2 Create `AuditLog` model in `Connect/core/models.py` (or `Connect/accounts/models.py`) per design spec; run migration
  - [ ] 16.3 Add `post_login` signal handler in `Connect/accounts/signals.py` — create `LoginEvent` and `AuditLog` records on every successful login
  - [ ] 16.4 Implement `RateLimitMiddleware` in `Connect/core/middleware.py` — track failed login attempts per IP in Redis; block IP for 15 min after 5 failures in 10 min window, return 429
  - [ ] 16.5 Wire `RateLimitMiddleware` into `MIDDLEWARE` in `settings/base.py`
  - [ ] 16.6 Implement "Remember Me" session expiry — extend session to 30 days when checkbox is checked
  - _Requirements: 2.7, 2.8, 2.9_

