"""
Core middleware — security headers and (future) rate limiting.
"""
from __future__ import annotations


class SecurityHeadersMiddleware:
    """
    Attach security-related HTTP response headers to every response.
    Add this to MIDDLEWARE in settings AFTER all other middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'same-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response


class RateLimitMiddleware:
    """
    Redis-backed per-IP rate limiting for authentication endpoints.

    Rules (applied in order — first match wins):
      • /api/auth/*  and  /accounts/login/  →  5 req / 600 s per IP
      • /accounts/forgot-password/          →  5 req / 600 s per IP

    When Redis is unavailable the middleware degrades gracefully and
    allows the request through (fail-open).

    Requires REDIS_URL in settings (used by Celery / channels as well).
    """

    AUTH_PREFIXES = (
        '/api/auth/',
        '/accounts/login/',
        '/accounts/forgot-password/',
    )
    LIMIT = 5
    WINDOW = 600  # seconds

    def __init__(self, get_response):
        self.get_response = get_response
        self._redis = None

    def _get_redis(self):
        if self._redis is not None:
            return self._redis
        try:
            import redis
            from django.conf import settings
            url = getattr(settings, 'REDIS_URL', None)
            if url:
                self._redis = redis.Redis.from_url(url, decode_responses=True)
        except Exception:
            pass
        return self._redis

    def __call__(self, request):
        if any(request.path.startswith(p) for p in self.AUTH_PREFIXES):
            client_ip = self._get_ip(request)
            if not self._allow(client_ip, request.path):
                from django.http import HttpResponse
                return HttpResponse(
                    'Too many requests. Please wait before trying again.',
                    status=429,
                    content_type='text/plain',
                )
        return self.get_response(request)

    def _get_ip(self, request) -> str:
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def _allow(self, ip: str, path: str) -> bool:
        r = self._get_redis()
        if r is None:
            return True  # degrade gracefully
        # Normalise path to a short prefix for the key
        prefix = path.split('/')[2] if path.count('/') >= 2 else 'auth'
        key = f'rl:{ip}:{prefix}'
        try:
            count = r.incr(key)
            if count == 1:
                r.expire(key, self.WINDOW)
            return count <= self.LIMIT
        except Exception:
            return True  # degrade gracefully if Redis is down
