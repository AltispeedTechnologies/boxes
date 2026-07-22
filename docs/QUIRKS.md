# Quirks and non-obvious behavior

Read this before changing auth, balances, packages, or payments.

---

## Users, groups, and “staff”

1. **Role checks are Django groups**, not only flags:
   - `CustomUser.has_staff_role()` → group `Staff`
   - `CustomUser.is_customer()` → group `Customer`
   - `CustomUser.is_admin()` → group `Admin`
   - `CustomUser.has_delivery_role()` → group `Delivery`
2. **`has_staff_role` is intentionally not named `is_staff`** so it does not shadow `AbstractUser.is_staff` (boolean used by Django admin).
3. URL decorator `is_staff` in `urls.py` checks **`has_staff_role()`**, not `user.is_staff`.
4. URL decorator `is_delivery` allows **Delivery or Staff** for floor routes
   (`delivery_urlpatterns`: check-in, search, picklist add). Delivery cannot reach
   mgmt, account edit, checkout, or customer payments.
5. Demo users are often in **both** Staff and Customer so staff can open customer routes.
6. **Django admin** still uses the boolean `is_staff` / superuser flags.

---

## Account.user vs UserAccount

- `Account.user` = creator/owner FK (`on_delete=SET(1)` → superuser id 1). Seeded accounts may all point at sysadmin.
- Customer portal and “which account is mine?” use **`UserAccount`**.
- Never treat `Account.user` as the customer login.

---

## Profile vs staff user edit

| Surface | Who can change | Account names |
|---------|----------------|---------------|
| `/profile/` | Self only | Linked accounts read-only; if **exactly one** `UserAccount`, saving name mirrors `Account.name` + primary alias |
| Staff `/users/update` | Any user | Full account/user/alias tooling via `user_edit.js` |

Profile endpoints must ignore client-supplied user ids and use `request.user`.

---

## Balance sign convention

- Stored `Account.balance` **negative means the customer owes money**.
- UI helpers (`hr_balance`, `format_negative`, payment “current balance”) invert the sign for display.
- Ledger math uses debit/credit columns; do not assume positive balance = debt.

---

## Package FK protection

Package FKs to Account, Carrier, and PackageType use **`RESTRICT`**. Deleting a carrier/type/account that still has packages fails at the DB layer — by design.

---

## Check-out gates

`verify_can_checkout` / checkout submit enforce business rules around unpaid balances and package `paid` flags. Staff reverse checkout exists (`check_out_packages_reverse`) for corrections.

---

## Email sending

1. Templates and rules live in DB (`EmailSettings`, `NotificationRule`, `EmailTemplate`).
2. Work items sit in `EmailQueue` until Celery `send_emails` runs.
3. **`GlobalSettings.email_sending`** is a hard off switch.
4. Recipients come from **`CustomUserEmail`** (and related user resolution), not only `User.email`.
5. Delivery is **Mailjet**, not Django SMTP (SMTP env vars are for framework mail).

---

## Stripe

- API key set in `BoxesConfig.ready()` from `STRIPE_API_KEY`.
- Webhooks: `stripe.Webhook.construct_event` with `STRIPE_ENDPOINT_SECRET`; handler is CSRF-exempt.
  Full endpoint setup (Dashboard events, Mailjet auth, Stripe CLI for boxes-dev):
  [SETUP.md → Configuring webhooks](SETUP.md#configuring-webhooks).
- Payment methods: DB cache (`StripePaymentMethod`) is reconciled to Stripe on list (`get_payment_methods`).
- Tax rates may be created in Stripe when enabling taxes on the charges screen (`tax_stripe_id` stored on GlobalSettings).
- `pass_on_fees` changes whether processing fees are added to the customer total.

---

## Auto-import packages

`models/`, `views/`, `tasks/`, `backend/` `__init__.py` files dynamically import every sibling module. Consequences:

- A syntax error in one module breaks imports for the whole package.
- New files must be `.py` in the right directory; subpackages need explicit imports in `urls.py` if not already covered.
- Circular imports can appear suddenly when adding shared helpers — prefer `backend/` for non-HTTP logic.

---

## create_user_from_account

`boxes/backend/account.py:create_user_from_account` is **synchronous**, not a Celery task. It creates an **inactive** user with a random username/password and a `UserAccount` link. Do not call `.delay()` on it.

---

## Static files and processjs

- Production uses hashed static filenames (`ManifestStaticFilesStorage`).
- `processjs` deletes stale JS artifacts; behavior differs for `DEBUG=True` vs `False`.
- After JS changes in prod-like env, run `./setup.sh update` or `manage.py processjs`.

---

## Images / OverwriteStorage

Logo fields use storage that **overwrites** the same name instead of appending random suffixes. Safe for fixed branding paths; surprising if you expect Django’s default non-clobber behavior.

---

## Picklist validation

`Picklist.clean()` requires **at least one** of `date` or `description`. `save()` always calls `clean()`.

---

## LOGIN_REDIRECT_URL

`settings.LOGIN_REDIRECT_URL` is `/profile/` (matches My Profile). Login still honors `next` when present.

---

## Secure storage

Report PDFs and similar non-public files go under `.secure_storage/` (`SECURE_ROOT`), not `public/media`. Do not expose this directory via NGINX static rules.

---

## Dependency updates

- Edit pins in `requirements.in`.
- Regenerate lockfile: `./env/bin/pip-compile --upgrade --output-file=requirements.txt requirements.in`
- Install with `./setup.sh update`.
- Commit message convention for pure bumps: **`Update dependencies`**.

---

## Migrations

Never hand-write migration files when Django can generate them:

```bash
./env/bin/python manage.py makemigrations
./env/bin/python manage.py migrate
```

---

## Tests

Sparse tests under `boxes/tests/`. Prefer Django test client with `override_settings(ALLOWED_HOSTS=["*"])` or live hits to the dev host with session cookies. Gunicorn often runs with `--reload` so code changes apply without full restart.

## URL decorator introspection

`is_staff` / `is_customer` use `functools.wraps` and set `access_tier` on the
wrapper so `inspect.unwrap` and `manage.py generate_docs` can resolve the real
view callable. Do not reintroduce bare wrappers without `wraps`.
