# Management commands (generated)

## `manage.py generate_docs`

Generate API reference docs under docs/api/ from the running codebase (routes, models, views, backend, tasks, settings, JS).

Generate all API reference pages.

## `manage.py processjs`

Runs collectstatic and cleans up old files

Execute collectstatic and JS cleanup for DEBUG vs production hashing.

## `manage.py seeddata`

Enqueue ``populate_seed_data`` Celery task.

Call ``populate_seed_data.delay()``.
