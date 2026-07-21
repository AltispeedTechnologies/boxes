# Database-backed settings map

Configuration is split between:

1. **Environment** (`/etc/boxes.env`) — secrets, infrastructure, Django security. See [SETTINGS.md](SETTINGS.md).
2. **PostgreSQL rows** — business rules and branding editable from the staff UI (this document).

Staff management screens live under `/mgmt/*`. There is no separate settings service: views read/write these models directly.

---

## 1. `GlobalSettings` (general business config)

| Model | Typical rows | UI | View module |
|-------|--------------|----|-------------|
| `boxes.models.GlobalSettings` | **Singleton-ish** — code paths treat **pk=1** as the live config | Management → General (`/mgmt/general`) | `boxes/views/mgmt/general.py` |

### Fields

| Field | Type | Purpose | UI control |
|-------|------|---------|------------|
| `name` | CharField(32) | Business / warehouse name (labels, invoices) | Text |
| `address1` | CharField(64) | Address line 1 | Text |
| `address2` | CharField(64) | Address line 2 (city/state/zip etc.) | Text |
| `website` | CharField(64) | Public website URL/text | Text |
| `email` | CharField(64) | Public contact email | Text |
| `phone_number` | CharField(20), null | Public phone | Text |
| `email_sending` | Boolean, default True | Master switch for outbound notification emails | Toggle |
| `taxes` | Boolean, default False | Whether tax is applied on customer payments | Toggle (also charges screen) |
| `tax_rate` | Decimal(4,2), null | Tax percentage (e.g. 8.25) | Numeric |
| `tax_stripe_id` | CharField(30), null | Stripe Tax Rate id synced when taxes enabled | Set by backend, not free-typed in normal flow |
| `pass_on_fees` | Boolean, default False | Whether Stripe processing fees are passed to the customer | Toggle |
| `source_image` | ImageField | Original uploaded logo | File upload |
| `login_image` | ImageField | Resized logo for login page | Derived on save |
| `label_image` | ImageField | Resized logo for labels | Derived on save |
| `navbar_image` | ImageField | Resized logo for navbar | Derived on save |
| `favicon_image` | ImageField | Favicon derivative | Derived on save |

### Save behavior quirks

- `save_general_settings` accepts multipart form data including `source_image`.
- `resize_and_save()` generates fixed-size derivatives into the other image fields using Pillow.
- Storage is `OverwriteStorage`: same relative names are overwritten instead of Django's default unique naming.
- Templates and label/PDF code expect a GlobalSettings row to exist (typically id=1 after setup).

### Consumers

- Invoice/payment tax and fee logic (`backend/invoice.py`, customer views)
- Email master enable (`tasks/emails.py` checks `email_sending`)
- Labels, login page, navbar branding
- PDF/report headers where business identity is shown

---

## 2. `EmailSettings` + `NotificationRule` + `EmailTemplate`

| Model | Rows | UI |
|-------|------|-----|
| `EmailSettings` | Effectively singleton (first/get) | `/mgmt/email/configure` |
| `NotificationRule` | Many, FK → EmailSettings | Same form (days + template pairs) |
| `EmailTemplate` | Many named templates | `/mgmt/email/templates` |

### `EmailSettings` fields

| Field | Purpose |
|-------|---------|
| `sender_name` | From name for Mailjet |
| `sender_email` | From address for Mailjet |
| `check_in_template` | FK → EmailTemplate used when packages are checked in (nullable `SET_NULL`) |


### Pitfall: `sender_email` and Mailjet

`sender_email` is the SMTP/API **From** address. It must match a sender that
Mailjet has verified for the API keys in `/etc/boxes.env`. Using an arbitrary
customer-facing contact address that is not verified will cause API send
failures even when keys and templates are correct. See [SETUP.md](SETUP.md)
(Mailjet sender pitfall).


### `NotificationRule` fields

| Field | Purpose |
|-------|---------|
| `email_settings` | Parent settings row |
| `days` | Age threshold in days (relative to package check-in / rule logic in email tasks) |
| `template` | EmailTemplate to enqueue when rule matches |

### `EmailTemplate` fields

| Field | Purpose |
|-------|---------|
| `name` | Admin label |
| `subject` | Email subject (may include placeholders) |
| `content` | Body HTML/text; edited with Jodit in the UI |

### Related operational tables (not "settings" but driven by them)

| Model | Role |
|-------|------|
| `EmailQueue` | Work queue: package + template awaiting send |
| `SentEmail` / `SentEmailContents` / `SentEmailPackage` / `SentEmailResult` | Audit trail and provider response |

**UI:** logs at `/mgmt/email/logs`; body fetch `GET /emails/<pk>/contents`.

**Master kill switch:** even with templates configured, `GlobalSettings.email_sending=False` suppresses sending.

---

## 3. `AccountChargeSettings` (aging / storage fees)

| Model | Rows | UI |
|-------|------|-----|
| `AccountChargeSettings` | Multiple rules | `/mgmt/charges` |

### Fields

| Field | Type | Purpose |
|-------|------|---------|
| `days` | Integer, null | Grace / initial days before charges or rule start |
| `price` | Decimal(8,2), null | Amount charged per frequency period |
| `package_type` | FK → PackageType, null | Scope rule to a type; null may mean default/global depending on task logic |
| `frequency` | Char `D`/`W`/`M`, null | Daily / Weekly / Monthly |
| `endpoint` | Integer, null | Optional end bound (days) for the rule window |

### How it is applied

Celery task `age_charges` (hourly at minute `:01`) reads these rules and calls:

- `assess_regular_charges` — windowed regular storage charges
- `assess_custom_charges` — per-type frequency-based charges

Ledger entries are written as debits (customer liability); `total_accounts` recomputes balances.

### Charges page also edits tax globals

`save_charge_settings` updates charge rule rows **and** may update `GlobalSettings.taxes`, `tax_rate`, `pass_on_fees`, and Stripe tax rate id via `get_tax_rate()` (creates/updates Stripe Tax Rate objects).

---

## 4. Catalog settings (not a key/value store)

These are first-class domain tables edited as lists from Management:

| Model | UI | Endpoints |
|-------|-----|-----------|
| `Carrier` | `/mgmt/packages/carriers` | GET page; POST `/mgmt/packages/carriers/update` |
| `PackageType` | `/mgmt/packages/types` | GET page; POST `/mgmt/packages/types/update` |
| `Account` list mgmt | `/mgmt/accounts` | Search/create flows; detail under `/accounts/<pk>/...` |

Carriers and package types are also loaded from `initial_data.json` on first setup.

---

## 5. Report configuration (user-defined, stored as JSON)

| Model | Field | Purpose |
|-------|-------|---------|
| `Report` | `name` | Unique report name |
| `Report` | `config` | JSON: selected fields, filters, date ranges, sort (see report details UI / `backend/reports.clean_config`) |
| `ReportResult` | status, progress, pdf_path | Generation state (not operator settings) |
| `Chart` | frequency, chart_data, total_data | Cached dashboard series |

Report configs are created/edited under `/reports/*` (staff). Regenerated by Celery `regenerate_report_data` every 30 minutes and on demand for PDF.

---

## 6. Operational sequences

| Model | Purpose | Mutated by |
|-------|---------|------------|
| `PackageSystemTrackingCode` | Prefix + last_number for internal tracking codes | Package create/check-in when system tracking is used |

Not exposed as a general settings page; treat as internal counter.

---

## 7. Quick reference: where to change what

| Want to change… | Store | Where |
|-----------------|-------|-------|
| Django secret, DB password, Stripe secret, Mailjet keys | Env file | `/etc/boxes.env` |
| Warehouse name, address, logos | DB | GlobalSettings / General UI |
| Turn off all notification emails | DB | GlobalSettings.email_sending |
| From-address and check-in template | DB | EmailSettings |
| “Email after N days” rules | DB | NotificationRule |
| Email body/subject copy | DB | EmailTemplate |
| Daily/weekly storage fees by type | DB | AccountChargeSettings |
| Tax rate / pass-on fees | DB | GlobalSettings (+ Charges UI) |
| Carriers / package types | DB | Carrier / PackageType mgmt |
| Report definitions | DB | Report.config JSON |
| Time zone, DEBUG, HTTPS cookies | Env | settings.py via env |

---

## 8. Initial fixture interaction

`loaddata initial_data.json` seeds groups, carriers, package types, queues, and some email templates. It does **not** fully replace GlobalSettings/EmailSettings/charge rules for a live site — operators must complete General, Email, and Charges configuration after install (or copy production data).

Demo users/passwords are created only by `seeddata` (dev path), not by production `setup.sh prod`.
