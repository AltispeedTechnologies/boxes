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
| **Stripe** | `STRIPE_API_KEY` for customer payments (environment, not only UI). |

**Accounts and Users** are operational data, not install configuration — they never show setup warnings.

## How flags refresh

1. **Server render** — staff pages get `mgmt_setup` from the `mgmt_setup_status` context processor (cached ~45s).  
2. **Cache invalidation** — every management settings save clears the cache.  
3. **Client refresh** — `static/js/setup_status.js` hooks successful AJAX to mgmt URLs and refreshes icons via `GET /mgmt/setup-status?refresh=1`. Opening the Management dropdown also soft-refreshes.  

Implementation: `boxes/backend/setup_status.py`.


## API keys in /etc/boxes.env

Keys are **not** edited in the web UI. **Management → General** (and the **API keys (env)** menu item) show whether each variable is set and looks valid:

| Variable | Purpose |
|----------|---------|
| `MJ_APIKEY_PUBLIC` / `MJ_APIKEY_PRIVATE` | Mailjet outbound email |
| `STRIPE_API_KEY` | Customer card payments |
| `STRIPE_ENDPOINT_SECRET` | Stripe webhooks (`whsec_…`) |
| `MAILJET_WEBHOOK_SECRET` or USER/PASSWORD | Optional webhook auth |

Secret values are never displayed. Fix by editing `/etc/boxes.env` on the server and restarting gunicorn/celery.


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

