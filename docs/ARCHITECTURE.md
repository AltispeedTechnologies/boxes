# Architecture

Boxes is a Django single-app warehouse parcel tracker: staff check packages in,
customers pay, staff check packages out. Runtime stack is Django + Gunicorn +
NGINX + PostgreSQL + Celery/RabbitMQ + Stripe + Mailjet.

## Layout

| Area | Location |
|------|----------|
| HTTP | `boxes/views/` (+ `mgmt/`, `packages/`, `reports/`) |
| Business logic (sync) | `boxes/backend/` |
| Background jobs | `boxes/tasks/` |
| Domain models | `boxes/models/` |
| URL access tiers | `boxes/urls.py` (`public` / `authenticated` / `staff` / `customer`) |
| Config (secrets/infra) | `/etc/boxes.env` → `boxes/settings.py` |
| Config (business) | PostgreSQL — see [DATABASE_SETTINGS.md](DATABASE_SETTINGS.md) |

Packages under `models/`, `views/`, `tasks/`, and `backend/` auto-import sibling
modules via `__init__.py` so `from boxes.views import *` works for URL wiring.

## Identity model (critical)

- **CustomUser** — login (`AUTH_USER_MODEL`); roles are **groups** (`Staff`,
  `Customer`, `Admin`) via `has_staff_role()` / `is_customer()` / `is_admin()`.
- **Account** — billing/parcel entity. `Account.user` is creator/owner
  (`on_delete=SET(1)`), **not** the customer portal link.
- **UserAccount** — login ↔ account for the customer portal.
- **CustomUserEmail** — notification addresses (Mailjet), not only `User.email`.

URL decorator `is_staff` checks **group** membership (`has_staff_role`), not
Django's boolean `user.is_staff` (admin flag). Decorators set
`access_tier` metadata for introspection and generated docs.

## Generated API reference

Route, model, view, task, and settings reference is **generated** from the
running code:

```bash
./env/bin/python manage.py generate_docs
```

Output: [api/index.md](api/index.md).

## Related human docs

- [SETUP.md](SETUP.md) — deploy
- [DATABASE_SETTINGS.md](DATABASE_SETTINGS.md) — settings stored in the DB
- [QUIRKS.md](QUIRKS.md) — non-obvious behavior
- [DEVELOPMENT.md](DEVELOPMENT.md) — boxes-dev workflow
