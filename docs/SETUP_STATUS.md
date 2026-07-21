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
