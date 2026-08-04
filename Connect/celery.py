"""
Celery application configuration for DevLink.

Workers are started with:
    celery -A Connect worker --loglevel=info

Beat scheduler (periodic tasks):
    celery -A Connect beat --loglevel=info \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler
"""

import os

from celery import Celery
from celery.schedules import crontab

# Default to development settings for local work; production containers should set DJANGO_SETTINGS_MODULE to Connect.settings.production.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Connect.settings.development')

app = Celery('Connect')

# Read Celery config from Django settings (keys prefixed with CELERY_).
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all INSTALLED_APPS.
app.autodiscover_tasks()


# ---------------------------------------------------------------------------
# Periodic task schedule
# ---------------------------------------------------------------------------
app.conf.beat_schedule = {
    # Phase 6: delete notifications older than 90 days — runs daily at 03:00 UTC
    'delete-old-notifications': {
        'task': 'notifications.tasks.delete_old_notifications',
        'schedule': crontab(hour=3, minute=0),
    },
    # Phase 7: aggregate daily statistics — runs daily at 02:00 UTC
    'aggregate-daily-stats': {
        'task': 'core.tasks.aggregate_daily_stats',
        'schedule': crontab(hour=2, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Utility task for verifying the Celery worker is running."""
    print(f'Request: {self.request!r}')
