# Development workflow

## Canonical environment

| Item | Value |
|------|-------|
| Container | LXD `boxes-dev` |
| User | `www-data` |
| Tree | `/var/www/mikes-boxes` (main checkout) |
| Site | `http://boxes.tsimonq2.internal/` |
| Env file | `/etc/boxes.env` |

Work and commit **inside the container** as `www-data` unless you intentionally maintain a host clone.

```bash
lxc exec boxes-dev -- sudo -u www-data bash -lc '
cd /var/www/mikes-boxes
source env/bin/activate
# work here
'
```

Git author in container: **Simon Quigley <squigley@altispeed.com>**.

### Stripe / Mailjet webhooks on boxes-dev

`http://boxes.tsimonq2.internal` is not reachable from Stripe Cloud. For payment
webhooks while developing in the container:

1. Install the [Stripe CLI](https://stripe.com/docs/stripe-cli) on a machine that
   can reach the container (often the LXD host).
2. Forward events:

   ```bash
   stripe listen --forward-to http://boxes.tsimonq2.internal/webhooks/stripe
   ```

3. Copy the CLI’s `whsec_…` into `/etc/boxes.env` as `STRIPE_ENDPOINT_SECRET`
   and restart gunicorn (and celery if it was not already running).

Full production setup (Dashboard endpoint, event list, Mailjet auth) is in
**[SETUP.md → Configuring webhooks](SETUP.md#configuring-webhooks)**.

### Feature worktrees

Parallel feature branches may live as sibling checkouts under `/var/www/wt-<name>`
(for example `/var/www/wt-polish` on `feat/polish`). Use the same env file and
the shared virtualenv when convenient:

```bash
lxc exec boxes-dev -- sudo -u www-data bash -lc '
cd /var/www/wt-polish
set -a && . /etc/boxes.env && set +a
PYTHONPATH=/var/www/wt-polish /var/www/mikes-boxes/env/bin/python manage.py check
'
```

Keep commits inside the worktree; do not mix uncommitted work across trees.

---

## Test logins (seed data)

Password for all: `changem3`

| Username | Groups (typical) |
|----------|------------------|
| `sysadmin` | Admin + Staff + Customer |
| `staff` | Staff + Customer |
| `customer` | Customer |
| *(assign Delivery group)* | Delivery (limited floor role) |

Created via `./setup.sh dev` → `seeddata` → `populate_seed_data` Celery task (requires worker).

---

## setup.sh commands

| Command | Actions |
|---------|---------|
| `./setup.sh prod` | pip install, migrate, loaddata, processjs |
| `./setup.sh dev` | prod steps + dev deps + `seeddata` |
| `./setup.sh update` | pip upgrade from requirements.txt, migrate, processjs |
| `./setup.sh check` | `manage.py check --deploy` |
| `./setup.sh test` | install dev deps, run `manage.py test boxes.tests` |
| `./setup.sh test-coverage` | same under coverage with `--fail-under=40` |
| optional 2nd arg | virtualenv directory name (default `env`) |

Local equivalents:

```bash
./setup.sh test
./setup.sh test-coverage
# or with an existing env:
./env/bin/python manage.py test boxes.tests
./env/bin/coverage run manage.py test boxes.tests
./env/bin/coverage report --fail-under=40
```

---

## Day-to-day

```bash
# Activate
source env/bin/activate

# Migrations after model edits
./env/bin/python manage.py makemigrations
./env/bin/python manage.py migrate

# Static/JS after frontend changes
./env/bin/python manage.py processjs

# Dependency bump
# 1) edit requirements.in
./env/bin/pip-compile --upgrade --output-file=requirements.txt requirements.in
# Dev/CI tools: edit requirements-dev.in then
./env/bin/pip-compile --upgrade --output-file=requirements-dev.txt requirements-dev.in
./setup.sh update
```

System packages for full stack: `nginx`, `postgresql`, `rabbitmq-server`, `python3-virtualenv`, `libpango1.0-dev` (WeasyPrint).

---

## User invite activation (stub)

Portal users created from an account (`create_user_from_account`) start
**inactive** with a random/unusable password. Full invite token email is **not**
implemented (Mailjet is used for package notifications, not Django auth mail).

Staff workflow today:

1. Prepare or re-lock a login:

   ```bash
   ./env/bin/python manage.py prepare_invite <username_or_id>
   ```

   Sets `is_active=False` and an unusable password (use `--keep-password` to
   only deactivate).

2. In **Django admin** → Users: set a password for the user.

3. Activate:

   ```bash
   ./env/bin/python manage.py prepare_invite --activate <username_or_id>
   ```

   or tick **Active** in admin.

4. Share credentials out of band until a password-reset token email is built.

---

## Adding features (checklist)

| Task | Steps |
|------|-------|
| New model field | Edit `boxes/models/*.py` → makemigrations → migrate → commit model+migration |
| New staff page/API | View under `views/` or `views/mgmt/` → path in `staff_urlpatterns` → JS using `ajax_request` |
| Shared authenticated page | `authenticated_urlpatterns` + `login_required` |
| Customer feature | `customer_urlpatterns`; resolve account via `UserAccount` |
| Celery job | `@shared_task` in `tasks/`; add beat entry in settings if scheduled |
| DB-backed setting | Prefer existing GlobalSettings / EmailSettings / AccountChargeSettings; document in DATABASE_SETTINGS.md |

---

## Code organization rules

- HTTP in `views/`; reusable non-HTTP logic in `backend/`.
- Long-running or scheduled work in `tasks/`.
- Do not leave temporary scripts under `/tmp` on host or container.
- Do not commit `env/`, `public/`, `.secure_storage/`, or secrets.

---

## Documentation map

| Doc | Contents |
|-----|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [SETUP.md](SETUP.md) | Production install (includes Stripe + Mailjet env vars) |
| [SETTINGS.md](SETTINGS.md) | Env vars |
| [DATABASE.md](DATABASE.md) | Models |
| [DATABASE_SETTINGS.md](DATABASE_SETTINGS.md) | Settings stored in DB |
| [API.md](API.md) | HTTP routes |
| [CELERY.md](CELERY.md) | Tasks |
| [FRONTEND.md](FRONTEND.md) | JS/templates |
| [QUIRKS.md](QUIRKS.md) | Gotchas |

Python modules also carry docstrings on classes and functions; keep them updated when behavior changes.

---

## CI

`.gitlab-ci.yml` defines pipeline checks used on GitLab:

- `lint_pycodestyle` / unit tests install **`requirements-dev.txt`**
- unit tests run under **coverage** with `--fail-under=40`
- `lint_bootstrap_version` requires a single Bootstrap CDN version in templates

Local ESLint via `package.json` is optional.

## API documentation

Regenerate the reference under `docs/api/` after route/model/view changes:

```bash
./env/bin/python manage.py generate_docs
```


## Database reset (clean instance)

```bash
./setup.sh reset
```

Flushes all application data, reloads `initial_data.json` (groups, carriers,
package types, demo logins), and ensures the inactive `system` user exists.
Does **not** run bulk Faker seed. Demo passwords: `changem3` for
`sysadmin`, `staff`, `customer`.

For bulk demo parcels after a clean reset:

```bash
./env/bin/python manage.py seeddata --sync --accounts 50 --packages 200
```

## Creating web (portal) accounts

Staff can create Customer-group portal logins in two places:

1. **Create New Customer** modal (check-in / account mgmt): tick
   “Create web login” and supply username + password.
2. **Account edit → Create web account** card: link a new login to an
   existing billing account.

APIs (staff, CSRF + session cookie):

- `POST /users/new` JSON — billing account; set `create_web_account` +
  `username`/`password` for an active portal login.
- `POST /accounts/<id>/members/create` JSON — web login for existing account.
- `POST /accounts/<id>/members/link` JSON — `{user_id}` or `{username}` + role.
- `GET /users/search?term=` — Select2-style user lookup.

Backend helpers live in `boxes.backend.account` and `boxes.backend.membership`.
The last active **owner** cannot be disassociated unless
`allow_last_owner=true`.

