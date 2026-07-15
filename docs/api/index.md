# API reference (generated)

This directory is produced by `manage.py generate_docs`. Do not hand-edit;
re-run the command after changing routes, models, views, tasks, or settings.

```bash
cd /var/www/mikes-boxes   # or your deploy root
./env/bin/python manage.py generate_docs
```

| Page | Source of truth |
|------|-----------------|
| [urls.md](urls.md) | Django URLConf + view callables |
| [models.md](models.md) | Model classes, fields, methods |
| [views.md](views.md) | View modules and callables |
| [backend.md](backend.md) | Non-HTTP business logic |
| [tasks.md](tasks.md) | Celery tasks + beat schedule |
| [settings.md](settings.md) | Django settings module values (non-secret) |
| [templatetags.md](templatetags.md) | Template filters/tags |
| [management.md](management.md) | Management commands |
| [javascript.md](javascript.md) | Static JS file headers and functions |

Human-written operational docs (setup, quirks, DB-backed settings map) live in
parent `docs/`.
