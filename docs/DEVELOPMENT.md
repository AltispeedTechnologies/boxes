# Development workflow

## Canonical environment

| Item | Value |
|------|-------|
| Container | LXD `boxes-dev` |
| User | `www-data` |
| Tree | `/var/www/mikes-boxes` |
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

Git author in container: **Simon Quigley \<squigley@altispeed.com\>**.

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
| `./setup.sh dev` | prod steps + `seeddata` |
| `./setup.sh update` | pip upgrade from requirements.txt, migrate, processjs |
| `./setup.sh check` | `manage.py check --deploy` |
| optional 2nd arg | virtualenv directory name (default `env`) |

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
./setup.sh update
```

System packages for full stack: `nginx`, `postgresql`, `rabbitmq-server`, `python3-virtualenv`, `libpango1.0-dev` (WeasyPrint).

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
| [SETUP.md](SETUP.md) | Production install |
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

`.gitlab-ci.yml` defines pipeline checks used on GitLab. Local ESLint via `package.json` is optional.

## API documentation

Regenerate the reference under `docs/api/` after route/model/view changes:

```bash
./env/bin/python manage.py generate_docs
```
