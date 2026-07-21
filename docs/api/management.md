# Management commands (generated)

## `manage.py bootstrap_demo`

Ensure system user, Customer group membership, and a demo billing account for the fixture customer login (idempotent).

The actual logic of the command. Subclasses must implement
this method.

## `manage.py generate_docs`

Generate API reference docs under docs/api/ from the running codebase (routes, models, views, backend, tasks, settings, JS).

Generate all API reference pages.

## `manage.py prepare_invite`

Set a user inactive (and optionally unusable password) so staff can finish invite activation via Django admin password set.

Prepare or activate the named user.

## `manage.py processjs`

Runs collectstatic and cleans up old files

Execute collectstatic and JS cleanup for DEBUG vs production hashing.

## `manage.py seeddata`

Populate development seed data. Use --sync to run in-process (no Celery worker required); default enqueues a Celery task.

The actual logic of the command. Subclasses must implement
this method.
