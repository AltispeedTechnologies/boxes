"""Pickup days, schedule rules, and package pickup reservations."""
from django.db import models


class PickupDay(models.Model):
    """A concrete calendar day available (or disabled) for customer pickup.

    is_active=False overrides a schedule rule so the day is closed even if
    a weekly rule would otherwise open it. Optional link to a staff Picklist.
    """
    date = models.DateField(unique=True)
    picklist = models.ForeignKey(
        "Picklist",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pickup_days",
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        status = "open" if self.is_active else "closed"
        return f"PickupDay {self.date} ({status})"


class PickupScheduleRule(models.Model):
    """Rule that generates open pickup days in a date window.

    recurrence:
      - none: a single day on start_date (weekday ignored)
      - weekly: every weekday from start_date through end_date (if set)
    weekday uses Python date.weekday() (0=Monday through 6=Sunday).
    """
    RECURRENCE_NONE = "none"
    RECURRENCE_WEEKLY = "weekly"
    RECURRENCE_CHOICES = [
        (RECURRENCE_NONE, "None"),
        (RECURRENCE_WEEKLY, "Weekly"),
    ]

    name = models.CharField(max_length=100)
    recurrence = models.CharField(
        max_length=16,
        choices=RECURRENCE_CHOICES,
        default=RECURRENCE_NONE,
    )
    weekday = models.PositiveSmallIntegerField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PackagePickupReservation(models.Model):
    """Customer reservation of a package for a specific pickup day."""
    package = models.OneToOneField(
        "Package",
        on_delete=models.CASCADE,
        related_name="pickup_reservation",
    )
    pickup_day = models.ForeignKey(
        PickupDay,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="pickup_reservations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reservation package={self.package_id} day={self.pickup_day_id}"
