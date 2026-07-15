"""Celery tasks for pickup day notifications."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def notify_pickup_day_cancelled(pickup_day_id: int) -> dict:
    """Notify customers when a pickup day with reservations is cancelled.

    Logs the cancellation and attempts to enqueue EmailQueue items when a
    "Pickup Day Cancelled" template exists. Safe to call repeatedly.
    """
    from boxes.backend.pickup import enqueue_pickup_cancellation_emails
    from boxes.models import PackagePickupReservation, PickupDay

    try:
        pickup_day = PickupDay.objects.get(pk=pickup_day_id)
    except PickupDay.DoesNotExist:
        logger.warning("notify_pickup_day_cancelled: day id=%s missing", pickup_day_id)
        return {"success": False, "reason": "missing"}

    reservations = (
        PackagePickupReservation.objects.filter(pickup_day=pickup_day)
        .select_related("package", "user")
    )
    count = reservations.count()
    logger.info(
        "Pickup day %s cancelled; %s reservation(s) to notify (users=%s)",
        pickup_day.date,
        count,
        list(reservations.values_list("user_id", flat=True).distinct()),
    )

    queued = enqueue_pickup_cancellation_emails(pickup_day)
    return {"success": True, "reservations": count, "queued": queued}
