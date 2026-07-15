# Boxes

Parcel tracking for warehouses: accept carrier packages, store them, bill
customers, and release on pickup.

Maintained by Altispeed Technologies as **Mike's Boxes**.

## Features

- Staff check-in / check-out, queues, labels, picklists
- Customer portal with Stripe payments
- Account ledger and aging charges
- Mailjet notification templates and rules
- Configurable reports (CSV/PDF) and charts

## Requirements

- Ubuntu 24.04 LTS (22.04 known to work, not actively tested)
- PostgreSQL 16, Python 3.12, RabbitMQ, NGINX, Gunicorn

## Quick start

Full install: **[docs/SETUP.md](docs/SETUP.md)**.

```bash
set -a && . /etc/boxes.env && set +a
./setup.sh prod    # or: ./setup.sh dev
```

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/api/](docs/api/index.md) | **Generated** API reference (routes, models, views, tasks, settings) |
| [docs/SETUP.md](docs/SETUP.md) | Production install |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design (short) |
| [docs/DATABASE_SETTINGS.md](docs/DATABASE_SETTINGS.md) | Business settings stored in PostgreSQL |
| [docs/QUIRKS.md](docs/QUIRKS.md) | Non-obvious behavior |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Development workflow |

Regenerate API docs after code changes:

```bash
./env/bin/python manage.py generate_docs
```

## Credits and license

```
Copyright 2024-2026 Altispeed Technologies
Author: Simon Quigley <squigley@altispeed.com>

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License in the LICENSE file for
more details.
```
