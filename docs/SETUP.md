# Setting up Boxes

Boxes is a Django project utilizing Celery, RabbitMQ, PostgreSQL, NGINX, and GUnicorn. This document details setting up Boxes manually, with considerations for each step.


## Related documentation

After completing setup, configure **business settings in the database** (General, Email, Charges) via the staff UI. Full maps:

- [SETTINGS.md](SETTINGS.md) — `/etc/boxes.env` variables
- [DATABASE_SETTINGS.md](DATABASE_SETTINGS.md) — GlobalSettings, email, charge rules
- [ARCHITECTURE.md](ARCHITECTURE.md) — system overview
- [CELERY.md](CELERY.md) — worker/beat tasks you just enabled
- [DEVELOPMENT.md](DEVELOPMENT.md) — day-to-day development
- [SETUP_STATUS.md](SETUP_STATUS.md) — management UI setup flags and env key checks

---

## Base server setup

Boxes has been tested on Ubuntu 24.04 LTS, and we aim to support the latest Ubuntu LTS. Deploy an instance of Ubuntu on a server with a public IP address.

General setup such as installing fail2ban, configuring SSH keys, and regularly installing system updates is an assumed part of installing the base server. This can be done using e.g. Ansible using [this internal playbook](https://gitlab.com/altispeed/internal/ansible/templates/playbooks/wsgi-deploy). If you are not using Ansible, continue through the setup steps.

This command will allow you to install all necessary dependencies:

```bash
sudo apt -y install nginx postgresql rabbitmq-server python3-virtualenv libpango1.0-dev
```

## Installing Boxes

Clone the Boxes repository in a location accessible to nginx. This could be in /var/www, /srv, etc. Ensure you set permissions correctly, such that e.g. www-data owns the repository.

A public repository can be found [on GitHub](https://github.com/AltispeedTechnologies/boxes), or internally at Altispeed [here](https://gitlab.com/altispeed/internal/dev/mikes-boxes).

Next, configure Boxes. Here is an example configuration file, installed at `/etc/boxes.env`:

```bash
# General settings
SECRET_KEY="{{ vault_boxes_django_secret_key }}"
ALLOWED_HOSTS="{{ boxes_url }}"
DEBUG="False"

# Logging settings
LOGGING_FILE="/var/log/mikes-boxes.log"
LOGGING_LEVEL="DEBUG"

# Database settings
DB_ENGINE="django.db.backends.postgresql"
DB_NAME="boxes"
DB_USER="{{ boxes_user }}"
DB_PASSWORD="{{ vault_boxes_user_password }}"
DB_HOST="localhost"
DB_PORT="5432"

# Mailjet settings
MJ_APIKEY_PUBLIC="{{ vault_boxes_mailjet_public }}"
MJ_APIKEY_PRIVATE="{{ vault_boxes_mailjet_private }}"

# Stripe settings (three separate secrets — not interchangeable)
# Public / publishable key (pk_test_… or pk_live_…)
STRIPE_PUBLISHABLE_KEY="{{ vault_boxes_stripe_publishable_key }}"
# Private / secret key (sk_test_… or sk_live_…) — server only
STRIPE_SECRET_KEY="{{ vault_boxes_stripe_secret_key }}"
# Webhook signing secret from Dashboard → Developers → Webhooks (whsec_…)
# See "Configuring webhooks" below. Not the same as pk_/sk_.
STRIPE_WEBHOOK_SECRET="{{ vault_boxes_stripe_webhook_secret }}"

# Optional Mailjet Event API webhook (invent secret; put same value on Event API URL)
# MAILJET_WEBHOOK_SECRET="long-random-string-you-invent"
# Mailjet Event API URL must be: https://<host>/webhooks/mailjet?secret=long-random-string-you-invent

# Celery settings
CELERY_BROKER_USER="{{ rabbitmq_user }}"
CELERY_BROKER_PASSWORD="{{ rabbitmq_password }}"
CELERY_BROKER_VHOST="{{ rabbitmq_vhost }}"
```

### Pitfall: Mailjet sender must be verified

API keys alone are not enough for outbound mail. Mailjet only accepts
messages whose **From** address (or domain) is verified in the Mailjet
account. That address is configured in the app under **Management → Emails**
as `EmailSettings.sender_email` (invite code may fall back to other defaults
if settings are incomplete).

If `sender_email` is a mailbox that was never added and **activated** as a
sender in Mailjet, the REST API returns errors such as an invalid From
address, and customers never receive check-in, invite, or pickup messages.

**Setup checklist:**

1. Set `MJ_APIKEY_PUBLIC` / `MJ_APIKEY_PRIVATE` in `/etc/boxes.env`.
2. In the Mailjet dashboard, add and **verify/activate** the address you will
   use as From (or authenticate the whole sending domain).
3. In Boxes, set **Management → Emails → sender email** to that same verified
   address (display name is free text).
4. Enable outbound sending (`GlobalSettings.email_sending` / email settings UI).
5. Confirm Celery workers are running so `send_emails` drains `EmailQueue`.

Do not commit personal or production mailbox addresses into example configs
in git; only document the verification requirement.



(Replace elements surrounded in {{ }} with actual values. You'll use these values in the next steps.)

Ensure you create `/var/log/mikes-boxes.log` and set the permissions to be the same user as the above repository.

If you are configuring a local development instance, you will want to add these values:

```bash
DEBUG="True"
SECURE_SSL_REDIRECT="False"
SESSION_COOKIE_SECURE="False"
CSRF_COOKIE_SECURE="False"
SECURE_HSTS_SECONDS="0"
SECURE_HSTS_INCLUDE_SUBDOMAINS="False"
SECURE_HSTS_PRELOAD="False"
SECURE_REFERRER_POLICY="no-referrer-when-downgrade"
SECURE_CROSS_ORIGIN_OPENER_POLICY="None"
```


### Pitfall: SPF and DKIM (deliverability / spam)

Even with valid API keys and a verified From address, messages often land in
spam until the **sending domain** has SPF and DKIM (and preferably DMARC)
configured. In Mailjet, use the domain authentication / DNS setup for the
domain of `EmailSettings.sender_email`, then publish the TXT records Mailjet
provides at your DNS host. Re-check Mailjet until the domain shows as
authenticated. This is separate from verifying an individual sender address.

### Invite and other email links

Signup invite links must point at the **app host**, not the marketing website
stored in General settings (`GlobalSettings.website`). The app builds absolute
links from ``ALLOWED_HOSTS`` in `/etc/boxes.env` (scheme from
``SECURE_SSL_REDIRECT``: `http` when SSL redirect is off, otherwise `https`).
Example: `ALLOWED_HOSTS="boxes.example.internal"` yields invite URLs like
`http://boxes.example.internal/signup/<token>/`.


## Configuring NGINX

Here is an example NGINX configuration file for a simple HTTP server:

```
server {
    listen 80;
    server_name {{ boxes_url }};

    location ~ ^/(static|media)/ {
        root {{ boxes_root }}/{{ boxes_url }}/public;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/boxes/boxes.sock;
    }
}
```

HTTP/3 is recommended, but requires the upstream [mainline NGINX package]() (and a different configuration location) under Ubuntu 24.04 LTS. Under 26.04 LTS, this should be fully supported.

Use this configuration for HTTP/3:

```
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    listen 443 quic reuseport;
    listen [::]:443 quic reuseport;
    add_header Alt-Svc 'h3=":443"; ma=86400' always;
    server_name {{ boxes_url }};

    location ~ ^/(static|media)/ {
        root {{ boxes_root }}/{{ boxes_url }}/public;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/boxes/boxes.sock;
    }
}
```

To ensure NGINX is configured correctly, be sure to run `nginx -t` as root before restarting the systemd service.

## Configuring PostgreSQL

Ensure the values you configure below match the values in `/etc/boxes.env`, specifically `DB_NAME`, `DB_USER`, and `DB_PASSWORD`.

First, get into the root PostgreSQL console via `sudo -u postgres psql`, then run:

```
CREATE DATABASE {{ DB_NAME }};
\c {{ DB_NAME }};
CREATE USER {{ DB_USER }} WITH PASSWORD '{{ DB_PASSWORD }}';
GRANT ALL PRIVILEGES ON DATABASE {{ DB_NAME }} TO {{ DB_USER }};
GRANT ALL PRIVILEGES ON SCHEMA public TO {{ DB_USER }};
```

Exit PostgreSQL. No need to restart the systemd unit.

## Configuring RabbitMQ

Ensure the values you configure below match the values in `/etc/boxes.env`, specifically `CELERY_BROKER_USER`, `CELERY_BROKER_PASSWORD`, and `CELERY_BROKER_VHOST`.

For a local development instance, it is possible to use the default vhost, setting `CELERY_BROKER_VHOST` to `/`.

Run these commands as root:

```bash
rabbitmqctl add_user {{ CELERY_BROKER_USER }} {{ CELERY_BROKER_PASSWORD }}
rabbitmqctl set_permissions -p {{ CELERY_BROKER_VHOST }} {{ CELERY_BROKER_USER }} ".*" ".*" ".*"
```

## Setting up Boxes

Change into the directory of the repository as the user owning it. For example, run:

```bash
sudo -u www-data /bin/bash
cd ~/{{ REPOSITORY }}
```

Then, run the following commands:

```bash
set -a && . /etc/boxes.env && set +a && ./setup.sh prod
```

This will install all necessary Python packages to run Boxes.

Finally, install these systemd units under `/etc/systemd/system/`:

celery-beat.service:
```
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User={{ boxes_user }}
Group={{ boxes_user }}
EnvironmentFile=/etc/boxes.env
WorkingDirectory={{ boxes_root }}/{{ boxes_url }}
ExecStart={{ boxes_root }}/{{ boxes_url }}/env/bin/celery -A boxes beat -l info --schedule=/run/boxes/celerybeat-schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

celery.service:
```
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=simple
User={{ boxes_user }}
Group={{ boxes_user }}
EnvironmentFile=/etc/boxes.env
WorkingDirectory={{ boxes_root }}/{{ boxes_url }}
ExecStart={{ boxes_root }}/{{ boxes_url }}/env/bin/celery -A boxes worker -l info --max-tasks-per-child=1
Restart=always

[Install]
WantedBy=multi-user.target
```

gunicorn.service:
```
[Unit]
Description=gunicorn daemon
After=network.target postgresql@{{ postgres_version }}-main.service
Before=nginx.service

[Service]
User={{ boxes_user }}
Group={{ boxes_user }}
WorkingDirectory={{ boxes_root }}/{{ boxes_url }}
RuntimeDirectory=boxes
RuntimeDirectoryMode=0755
EnvironmentFile=/etc/boxes.env
ExecStart={{ boxes_root }}/{{ boxes_url }}/env/bin/gunicorn --reload --access-logfile - --workers 5 --bind unix:/run/boxes/boxes.sock boxes.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Once you're done, enable and start these services as root:

```bash
systemctl daemon-reload && systemctl enable --now celery-beat celery gunicorn
```

This may take a second, but should output successfully for all three units:

```bash
systemctl status celery-beat celery gunicorn
```


## Configuring webhooks

Boxes receives payment and email-delivery events from external providers on two public
POST endpoints (CSRF-exempt, no session cookie required):

| Provider | Path | Env secret / auth |
|----------|------|-------------------|
| Stripe | `/webhooks/stripe` | `STRIPE_WEBHOOK_SECRET` (`whsec_…`) only — not `pk_`/`sk_` |
| Mailjet | `/webhooks/mailjet` | Optional `MAILJET_WEBHOOK_SECRET` (same value as `?secret=` on Event API URL) |

Full URL examples (replace with your real host from `ALLOWED_HOSTS`):

- Production: `https://boxes.example.com/webhooks/stripe`
- Production: `https://boxes.example.com/webhooks/mailjet`
- Internal / dev: `http://boxes.tsimonq2.internal/webhooks/stripe`

NGINX must proxy these paths to Gunicorn like any other app URL (the default
`location /` config already does). Celery workers must be running: Stripe
payment handling is enqueued with `handle_stripe_webhook.delay(...)`.

After changing `/etc/boxes.env`, restart the app processes:

```bash
sudo systemctl restart gunicorn celery celery-beat
```

Check status under **Management → API keys (env)** (or **General**):
`STRIPE_WEBHOOK_SECRET` should show OK with a `whsec_…` format, and Mailjet
webhook auth should show as set when you configure it.

### Stripe webhook (required for card payments)

Without a correctly signed Stripe endpoint, Checkout / PaymentIntent events
never mark invoices paid or update package balances.

**1. API keys (public + private — separate from the webhook secret)**

In [Stripe Dashboard](https://dashboard.stripe.com/) → **Developers → API keys**:

1. Copy the **Publishable key** (`pk_live_…` or `pk_test_…`) into
   `STRIPE_PUBLISHABLE_KEY`.
2. Copy the **Secret key** (`sk_live_…` or `sk_test_…`) into
   `STRIPE_SECRET_KEY`.

Use a matching test or live pair only. These are **not** the webhook signing
secret (`whsec_…` goes in `STRIPE_WEBHOOK_SECRET` in the next step).

**2. Create the webhook endpoint**

1. Open **Developers → Webhooks → Add endpoint**.
2. **Endpoint URL:** `https://{{ boxes_url }}/webhooks/stripe`
   (must be reachable from the public internet for Stripe Cloud; use the
   [Stripe CLI](https://stripe.com/docs/stripe-cli) only for local tunneling).
3. **Events to send** — select at least these PaymentIntent events (the app
   rejects other event types with HTTP 400):

   - `payment_intent.succeeded`
   - `payment_intent.canceled`
   - `payment_intent.payment_failed`

4. Create the endpoint, then open it and **Reveal** the **Signing secret**.
5. Put that value in `/etc/boxes.env` as:

   ```bash
   STRIPE_WEBHOOK_SECRET="whsec_…"
   ```

6. Restart gunicorn and celery (command above).

**3. Verify**

- Stripe Dashboard → Webhooks → your endpoint → **Send test webhook** for
  `payment_intent.succeeded`. A valid signature with a PaymentIntent the app
  does not know about still returns **200** after enqueue (handler no-ops if
  no matching `Invoice`); a bad secret returns **400**.
- App logs (`LOGGING_FILE`, often `/var/log/mikes-boxes.log`) warn on
  `Error verifying Stripe webhook signature` when the secret is wrong.
- Complete a test Checkout payment: invoice should move to paid and packages
  should mark paid after Celery processes the task.

**Common mistakes**

| Symptom | Likely cause |
|---------|----------------|
| HTTP 400, signature errors in log | Wrong `STRIPE_WEBHOOK_SECRET`, or secret from a different endpoint/mode (test vs live) |
| HTTP 400, no signature error | Event type not one of the three `payment_intent.*` events above |
| 200 but invoice never paid | Celery worker down, or PaymentIntent id not stored on an `Invoice` row |
| Stripe cannot deliver | Host not public / TLS / firewall; wrong path (must be `/webhooks/stripe`, no trailing slash required) |
| Secret format warning in Management UI | Value does not start with `whsec_` |

**Local / container development**

Internal hosts such as `http://boxes.tsimonq2.internal` are not reachable by
Stripe Cloud. Options:

1. **Stripe CLI** (recommended for dev):

   ```bash
   stripe listen --forward-to http://boxes.tsimonq2.internal/webhooks/stripe
   ```

   The CLI prints a temporary `whsec_…`. Put that in `/etc/boxes.env` as
   `STRIPE_WEBHOOK_SECRET` and restart gunicorn. Use `stripe trigger
   payment_intent.succeeded` only for delivery checks; real payment flow still
   needs a Checkout/PaymentIntent created by the app.

2. Or expose the site with a tunnel (ngrok, etc.) and register that HTTPS URL
   as the Dashboard endpoint.

Keep **test** API keys and the matching test-mode webhook secret together;
never mix live secrets with test keys.

### Mailjet webhook (email delivery events)

Optional but recommended for delivery audit (`SentEmailEvent`). Outbound mail
only needs `MJ_APIKEY_PUBLIC` / `MJ_APIKEY_PRIVATE` and a verified From.

Mailjet does **not** issue a signing secret. You invent one value and set it in
**two** places only (no username/password).

#### 1. Boxes: `/etc/boxes.env`

```bash
MAILJET_WEBHOOK_SECRET="long-random-string-you-invent"
```

Restart gunicorn after editing:

```bash
sudo systemctl restart gunicorn
```

#### 2. Mailjet UI: Event API callback URL

1. Mailjet dashboard → **Account settings** → **Event API** (or Event
   notifications / webhooks, depending on product UI).
2. Set the **endpoint URL** to **exactly** (same secret as above):

   ```text
   https://{{ boxes_url }}/webhooks/mailjet?secret=long-random-string-you-invent
   ```

   The path is `/webhooks/mailjet`. The query parameter name is `secret`.
   That is the only place in the Mailjet UI where the shared secret is set
   (embedded in the URL). Boxes also accepts header
   `X-Mailjet-Webhook-Secret` for tests; the Event API UI does not send it.
3. Enable events (Boxes stores any type; no allowlist):

   | Event | Recommended |
   |-------|-------------|
   | `sent` | Yes |
   | `bounce` | Yes |
   | `blocked` | Yes |
   | `spam` | Yes |
   | `open` | Optional |
   | `click` | Optional |
   | `unsub` | Optional |

   Minimum useful set: **sent**, **bounce**, **blocked**, **spam**.
4. Save.

If `MAILJET_WEBHOOK_SECRET` is unset, Boxes accepts all POSTs and logs a warning
(dev only). Wrong or missing `?secret=` with the env var set returns **401**.

**Common mistakes**

| Symptom | Likely cause |
|---------|----------------|
| HTTP 401 | Env secret set but Mailjet URL missing/wrong `?secret=` |
| Events not linked to SentEmail | No matching `Message_GUID` on send |
| Open endpoint warning in logs | `MAILJET_WEBHOOK_SECRET` not set |


---

## Completion

Setup should now be complete. Before going live, finish **[Configuring webhooks](#configuring-webhooks)**
(Stripe is required for payment confirmation; Mailjet Event API is recommended
for delivery audit). Confirm **Management → API keys (env)** shows the required
keys as OK, and that Celery is processing tasks.

If something here is incorrect, please correct it once running through these instructions.
