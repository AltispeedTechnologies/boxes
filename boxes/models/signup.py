"""Tokenized customer self-registration invites (link-only signup)."""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


def default_invite_expiry():
    """Default invite lifetime: 14 days from now."""
    return timezone.now() + timedelta(days=14)


def generate_invite_token():
    """Return a high-entropy URL-safe invite token."""
    return get_random_string(48)


class SignupInvite(models.Model):
    """One-time sign-up invitation. Registration is only allowed via a valid token.

    Staff create invites (and optionally a billing Account to link on accept).
    Customers complete registration at ``/signup/<token>/`` only — there is no
    open public registration endpoint.
    """

    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_invite_token)
    email = models.EmailField(max_length=254)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    middle_name = models.CharField(max_length=64, blank=True, default="")
    prefix = models.CharField(max_length=16, blank=True, default="")
    suffix = models.CharField(max_length=16, blank=True, default="")
    company = models.CharField(max_length=128, blank=True, default="")
    phone_number = models.CharField(max_length=20, blank=True, default="")
    mobile_number = models.CharField(max_length=20, blank=True, default="")

    # Optional pre-created billing account to associate when the invite is accepted
    account = models.ForeignKey(
        "Account",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="signup_invites",
    )
    role = models.CharField(max_length=16, default="owner")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_signup_invites",
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default=default_invite_expiry)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accepted_signup_invites",
    )
    email_sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "used_at"]),
        ]

    def __str__(self):
        status = "used" if self.used_at else ("expired" if self.is_expired() else "pending")
        return f"SignupInvite({self.email}, {status})"

    def is_expired(self):
        """True if past expires_at."""
        return timezone.now() >= self.expires_at

    def is_usable(self):
        """True if not used and not expired."""
        return self.used_at is None and not self.is_expired()
