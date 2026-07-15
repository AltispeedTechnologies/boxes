# Celery tasks (generated)

## Beat schedule

From `settings.CELERY_BEAT_SCHEDULE`:

| Name | Task | Schedule |
|------|------|----------|
| `age_charges` | `boxes.tasks.charges.age_charges` | `<crontab: 1 * * * * (m/h/dM/MY/d)>` |
| `age_picklists` | `boxes.tasks.maintenance.age_picklists` | `<crontab: 0 3 * * * (m/h/dM/MY/d)>` |
| `regenerate_report_data` | `boxes.tasks.maintenance.regenerate_report_data` | `<crontab: */30 * * * * (m/h/dM/MY/d)>` |
| `remove_old_coupons` | `boxes.tasks.stripe.remove_old_coupons` | `<crontab: 3 * * * * (m/h/dM/MY/d)>` |
| `send_emails` | `boxes.tasks.emails.send_emails` | `<crontab: */10 * * * * (m/h/dM/MY/d)>` |
| `total_accounts` | `boxes.tasks.charges.total_accounts` | `<crontab: 2 * * * * (m/h/dM/MY/d)>` |


## `boxes.tasks`

Auto-import Celery task modules.

## `boxes.tasks.charges`

Aging storage fees and account balance totals.

### `get_frequency_delta(frequency)`

Return a timedelta object based on the frequency.

## `boxes.tasks.emails`

Mailjet notification sending from EmailQueue.

## `boxes.tasks.maintenance`

Picklist aging, seed data, and report refresh tasks.

## `boxes.tasks.pdf`

WeasyPrint report PDF generation.

### class `PDFLoggingHandler`

Logging handler that updates ReportResult progress from log records.

- `__init__(self, result, level=0)` — Attach handler to a ReportResult instance.
- `emit(self, record)` — Update progress field from log record messages.

## `boxes.tasks.pickup`

Celery tasks for pickup day notifications.

## `boxes.tasks.stripe`

Stripe webhook processing and coupon cleanup.

### `process_successful_invoice(user_id, account_id, invoice_id, subtotal, line_items)`

Apply successful payment to ledger and mark packages paid.
