import logging
from celery import shared_task
from apps.analytics.services import AnalyticsRollupService

logger = logging.getLogger(__name__)


@shared_task(name="apps.analytics.tasks.rollup_daily_analytics_task")
def rollup_daily_analytics_task():
    """
    Celery Beat scheduled job to compile yesterday's platform metrics and refresh snapshots.
    """
    logger.info("Executing periodic analytics rollup task...")
    try:
        metric = AnalyticsRollupService.compute_daily_snapshot()
        logger.info("Successfully computed daily snapshot for %s", metric.date)
        return {"status": "SUCCESS", "date": str(metric.date)}
    except Exception as e:
        logger.error("Failed to compute daily analytics snapshot: %s", e)
        return {"status": "FAILED", "error": str(e)}
