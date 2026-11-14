import logging
from celery import shared_task

logger = logging.getLogger("notifications.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def deliver_notification_task(self, delivery_id):
    """Deliver a logged notification asynchronously via Celery worker."""
    from apps.notifications.services import deliver_notification
    try:
        result = deliver_notification(delivery_id)
        return f"Notification {delivery_id} delivered (status={getattr(result, 'status', 'unknown')})"
    except Exception as exc:
        logger.error("Error executing deliver_notification_task for %s: %s", delivery_id, exc)
        raise self.retry(exc=exc)
