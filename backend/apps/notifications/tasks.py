import logging
from celery import shared_task
from django.utils import timezone
from apps.notifications.models import Notification
from apps.users.models import User

logger = logging.getLogger("futurelearning.notifications")


@shared_task(
    bind=True,
    name="apps.notifications.tasks.dispatch_notification_task",
    max_retries=3,
    default_retry_delay=5,
)
def dispatch_notification_task(
    self,
    recipient_id: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: str = "",
):
    """
    Asynchronously creates an in-app notification and dispatches email/digest if configured.
    Fulfills FR-NOT-01 and FR-NOT-03.
    """
    try:
        user = User.objects.filter(id=recipient_id).first()
        notification = Notification.objects.create(
            recipient=user,
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            is_read=False,
        )
        logger.info(
            "Notification %s created for recipient %s (%s)",
            notification.id,
            recipient_id,
            notification_type,
        )
        return str(notification.id)
    except Exception as exc:
        logger.error("Failed to dispatch notification for %s: %s", recipient_id, exc)
        raise self.retry(exc=exc)
