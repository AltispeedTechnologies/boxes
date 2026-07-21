"""Prepare a CustomUser for invitation (inactive until password is set).

Invite activation is intentionally a stub: staff prepare the account, set a
password (or unusable password), and complete onboarding via Django admin.
Prefer staff UI **Management → Users → Send invite** (or POST /users/new with
``send_invite``) for tokenized self-registration at ``/signup/<token>/``.
This command remains a low-level helper for deactivating a user until a password
is set in admin.
"""
from django.core.management.base import BaseCommand, CommandError

from boxes.models import CustomUser


class Command(BaseCommand):
    """Mark a user inactive for invite-style activation via admin."""

    help = (
        "Set a user inactive (and optionally unusable password) so staff can "
        "finish invite activation via Django admin password set."
    )

    def add_arguments(self, parser):
        """Register CLI options."""
        parser.add_argument(
            "user",
            help="Username or numeric primary key of the CustomUser to prepare",
        )
        parser.add_argument(
            "--keep-password",
            action="store_true",
            help="Do not replace the password with an unusable password",
        )
        parser.add_argument(
            "--activate",
            action="store_true",
            help="Set is_active=True instead (complete invite after password set)",
        )

    def handle(self, *args, **options):
        """Prepare or activate the named user."""
        key = options["user"]
        user = self._resolve_user(key)

        if options["activate"]:
            if not user.has_usable_password():
                raise CommandError(
                    f"User {user.username!r} has an unusable password; "
                    "set a password in Django admin before activating."
                )
            user.is_active = True
            user.save(update_fields=["is_active"])
            self.stdout.write(self.style.SUCCESS(
                f"Activated user {user.username!r} (pk={user.pk})."
            ))
            return

        user.is_active = False
        update_fields = ["is_active"]
        if not options["keep_password"]:
            user.set_unusable_password()
            update_fields.append("password")
        user.save(update_fields=update_fields)

        self.stdout.write(self.style.SUCCESS(
            f"Prepared invite for user {user.username!r} (pk={user.pk}): "
            f"is_active=False"
            + ("" if options["keep_password"] else ", unusable password")
            + "."
        ))
        self.stdout.write(
            "Next steps:\n"
            "  1. Django admin → Users → set a password for this user\n"
            "  2. Tick Active, or run: manage.py prepare_invite --activate "
            f"{user.username}\n"
            "  3. Share credentials out of band (token email not implemented; "
            "Mailjet is for package notifications only)."
        )

    def _resolve_user(self, key: str) -> CustomUser:
        if key.isdigit():
            user = CustomUser.objects.filter(pk=int(key)).first()
            if user:
                return user
        user = CustomUser.objects.filter(username=key).first()
        if user:
            return user
        raise CommandError(f"No CustomUser found for {key!r}")
