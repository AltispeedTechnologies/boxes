# Management setup completeness

Fresh installs need configuration before Boxes is fully usable. The **Management** navbar dropdown shows a warning icon next to items that still need attention, and a warning on the Management label when anything is incomplete.

## Required (core warehouse use)

| Item | Why |
|------|-----|
| **General** | Business name, address, and email or phone for labels and invoices (not empty defaults). Logo is recommended. |
| **Carriers** | At least one **active** carrier for check-in. |
| **Package Types** | At least one **active** package type with pricing for check-in. |

## Recommended

| Item | Why |
|------|-----|
| **Charges** | Aging / storage fee rules (`age_charges`). Without rules, fees do not auto-age. |
| **Emails** | Sender name/address, check-in template, Mailjet keys when `email_sending` is on. |
| **Email Templates** | At least one template when email is enabled. |
| **Pickup Days** | Schedule rules or open days for customer pickup reservations. |
| **Stripe** | `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, and `STRIPE_WEBHOOK_SECRET` (environment, not only UI). |
| **HTTP Connectivity** | Browser reports protocol via Navigation Timing (`nextHopProtocol`). Warns when not HTTP/3 (HTTP/1.1 or HTTP/2). Configure NGINX QUIC as in [SETUP.md](SETUP.md). |

**Accounts and Users** are operational data, not install configuration — they never show setup warnings.

Banner issue lists are de-duplicated: Stripe/Mailjet key details appear under **API Keys and Environment** only; related menu items use a single summary line.

## How flags refresh

1. **Server render** — staff pages get `mgmt_setup` from the `mgmt_setup_status` context processor (cached ~45s).  
2. **Cache invalidation** — every management settings save clears the cache.  
3. **Client refresh** — `static/js/setup_status.js` hooks successful AJAX to mgmt URLs and refreshes icons via `GET /mgmt/setup-status?refresh=1`. Opening the Management dropdown also soft-refreshes.  

Implementation: `boxes/backend/setup_status.py`.


## API keys in /etc/boxes.env

Keys are **not** edited in the web UI. **Management → General** (and the **API keys (env)** menu item) show whether each variable is set and looks valid:

| Variable | Purpose |
|----------|---------|
| `MJ_APIKEY_PUBLIC` | Mailjet public API key (outbound email) |
| `MJ_APIKEY_PRIVATE` | Mailjet private API key (outbound email) |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key (`pk_…`) |
| `STRIPE_SECRET_KEY` | Stripe private key (`sk_…`, server-side) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_…`) for `/webhooks/stripe` |
| `MAILJET_WEBHOOK_SECRET` | Invent in `/etc/boxes.env`; same value on Mailjet Event API URL as `?secret=` |

Secret values are never displayed. Fix by editing `/etc/boxes.env` on the server and restarting gunicorn/celery.

### Setting up the webhook endpoints

Env vars alone are not enough: you must also register the public URLs with
Stripe and (optionally) Mailjet. Step-by-step instructions, required event
types, auth options, and troubleshooting live in
**[SETUP.md → Configuring webhooks](SETUP.md#configuring-webhooks)**.

Summary:

| Integration | Endpoint | Required? |
|-------------|----------|-----------|
| Stripe | `https://<host>/webhooks/stripe` | Yes for payment confirmation |
| Mailjet Event API | `https://<host>/webhooks/mailjet` | Optional (delivery audit) |

Stripe must send `payment_intent.succeeded`, `payment_intent.canceled`, and
`payment_intent.payment_failed`. Paste the Dashboard **Signing secret** into
`STRIPE_WEBHOOK_SECRET`. For local/container hosts that Stripe cannot reach,
use the Stripe CLI (`stripe listen --forward-to …`) and its printed `whsec_…`.


## Pitfall: verified Mailjet From address

Even when `MJ_APIKEY_*` show as OK under **API keys (env)**, outbound mail fails
if **Management → Emails → sender email** is not a **verified sender** (or a
mailbox on a verified domain) in Mailjet. The management UI checks env key
presence/format only; it does not call Mailjet to validate the From address.

When debugging silent non-delivery:

1. Confirm sender email in **Emails** matches a verified Mailjet sender.
2. Inspect recent `SentEmail` rows (`success`, `SentEmailResult.response`).
3. For invites, check `SignupInvite.last_error` / `email_sent_at`.
4. Ensure Celery workers process `boxes.tasks.emails.send_emails` for queue mail.

## Pitfall: SPF / DKIM

Verify the sending domain in Mailjet (SPF + DKIM DNS records) so transactional
mail is less likely to be classified as spam. Address verification alone is
often insufficient for inbox placement.

