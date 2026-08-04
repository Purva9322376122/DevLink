"""
Custom DRF exception handler.

Wraps all API error responses in a consistent envelope:
    {
        "error": "<human-readable message>",
        "code":  "<machine-readable code>",
        "details": { ... }   # field-level validation errors, if any
    }

Register in settings:
    REST_FRAMEWORK = {
        ...
        'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    }
"""
from __future__ import annotations

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    detail = response.data

    # Flatten DRF's default structure into our envelope
    if isinstance(detail, dict):
        # Field-level validation errors
        human = "Validation failed."
        code = "validation_error"
        details = detail
    elif isinstance(detail, list):
        human = str(detail[0]) if detail else "An error occurred."
        code = getattr(detail[0], 'code', 'error') if detail else 'error'
        details = {}
    else:
        human = str(detail)
        code = getattr(detail, 'code', 'error')
        details = {}

    response.data = {
        'error': human,
        'code': code,
        'details': details,
    }

    return response
