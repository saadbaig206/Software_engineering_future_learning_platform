import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("futurelearning")

# Read configuration from Django settings, using the CELERY namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=False)
def debug_smoke_task(self, message="FutureLearning Celery Worker Alive"):
    """Smoke-test task to verify Celery broker, worker, and result backend."""
    return {
        "status": "SUCCESS",
        "task_id": self.request.id,
        "message": message,
    }


# Celery Beat Periodic Tasks Configuration (FR-ANL-03)
app.conf.beat_schedule = {
    "daily-analytics-rollup": {
        "task": "apps.analytics.tasks.rollup_daily_analytics_task",
        "schedule": 86400.0,  # Once every 24 hours
    },
}
