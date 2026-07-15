# Backend (generated)

Public callables discovered under `boxes.backend`.

## `boxes.backend`

Auto-import backend business-logic modules.

## `boxes.backend.account`

Account-related non-HTTP helpers.

### `create_user_from_account(account_id)`

Create an inactive CustomUser linked to an account via UserAccount.

Returns the user id, or an existing linked user id, or None if the account is missing/empty name.
Synchronous — not a Celery task. Username is a random unique string.

## `boxes.backend.invoice`

Stripe customer, payment methods, and invoice line-item construction.

### `generate_checkout_line_items(line_items, tax_rate_id)`

Convert internal line items into Stripe checkout/PaymentIntent line structure.

### `generate_line_items(amount, user_id)`

Allocate a payment ``amount`` across unpaid checked-in packages for the user.

Returns structured line items (package id, amount, partial/late flags) or None if amount <= 0.

### `get_billing_portal_id()`

Return Stripe Billing Portal configuration id, creating a default if absent.

### `get_customer_id(user_id)`

Return Stripe customer id for the account linked to ``user_id``, creating if needed.

### `get_payment_method_json(pm, pm_id)`

Map a Stripe payment method object to a light UI dict (id, brand, last4).

### `get_payment_methods(user_id)`

Sync DB payment methods with Stripe and return (list, default_method).

## `boxes.backend.reports`

Report query building, config cleaning, and chart data generation.

### `clean_config(config)`

Normalize and validate a report config dict from the UI.

### `generate_full_report(pk)`

Execute report ``pk`` config against the ORM and return tabular result data.

### `report_chart_generate(timeframe_filter)`

Build chart series data for the given timeframe filter.
