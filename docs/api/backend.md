# Backend (generated)

Public callables discovered under `boxes.backend`.

## `boxes.backend`

Auto-import backend business-logic modules.

## `boxes.backend.account`

Account-related non-HTTP helpers.

### `activate_web_user(user, password=None)`

Activate a portal user, optionally setting a new password.

### `create_account_with_web_user(*, actor, username, password, first_name, last_name='', middle_name='', prefix='', suffix='', company='', phone_number='', mobile_number='', email=None, account_name=None, billable=True, comments=None, is_active=True)`

Create a billing Account and a portal login linked as owner.

``account_name`` defaults to the composed person name. Returns dict with
account, user, and membership.

### `create_billing_account(*, actor, name, billable=True, comments=None, balance=None, owner_user=None)`

Create an Account (+ balance + primary alias), optionally owned by ``owner_user``.

``actor`` is stored as Account.user (creator). Returns the Account.

### `create_user_from_account(account_id)`

Create an inactive CustomUser linked to an account via UserAccount.

Returns the user id when a single membership exists or a new user is
created. Returns an existing linked user id only when there is exactly one
membership. Returns None if the account is missing, has an empty name, or
already has multiple linked users (ambiguous). Creates a user only when
there are zero memberships.

### `create_web_user(*, username, password, first_name, last_name='', middle_name='', prefix='', suffix='', company='', phone_number='', mobile_number='', email=None, is_active=True, account=None, role='owner', actor=None)`

Create an active portal login (Customer group) and optionally link to ``account``.

Validates password strength and username uniqueness. Returns (user, membership|None).

### `ensure_account_balance(account)`

Create zero ``AccountBalance`` row if missing.

### `ensure_customer_group(user)`

Ensure ``user`` is in the Customer group (portal access).

## `boxes.backend.invoice`

Stripe customer, payment methods, and invoice line-item construction.

### `generate_checkout_line_items(line_items, tax_rate_id)`

Convert internal line items into Stripe checkout/PaymentIntent line structure.

### `generate_line_items(amount, account_id)`

Allocate a payment ``amount`` across unpaid checked-in packages for the account.

Returns structured line items (package id, amount, partial/late flags) or None if amount <= 0.

### `get_billing_portal_id()`

Return Stripe Billing Portal configuration id, creating a default if absent.

### `get_customer_id(account_id)`

Return Stripe customer id for ``account_id``, creating if needed.

### `get_payment_method_json(pm, pm_id)`

Map a Stripe payment method object to a light UI dict (id, brand, last4).

### `get_payment_methods(account_id)`

Sync DB payment methods with Stripe and return (list, default_method).

## `boxes.backend.membership`

CustomUser ↔ Account membership helpers (portal multi-account support).

### `associate_user(account, user, role='member', actor=None)`

Link ``user`` to ``account`` idempotently; reactivate if soft-disabled.

``actor`` is reserved for future audit logging.

### `clear_active_account_if_matches(request, account_id)`

Drop session active account when it matches ``account_id``.

### `disassociate_user(account, user, actor=None, *, allow_last_owner=False)`

Soft-disable membership (``is_active=False``). No-op if missing.

Refuses to deactivate the last active owner unless ``allow_last_owner``.
``actor`` is reserved for future audit logging. Returns the membership or None.

### `get_active_account(request)`

Resolve the request user active Account from session / memberships.

Session key: ``active_account_id``. If missing/invalid and the user has
exactly one active membership, that account is returned. If the user has
multiple active memberships and no valid session selection, returns None.

### `get_membership(user, account, active_only=True)`

Return UserAccount row for user+account, or None.

### `list_accounts_for_user(user, active_only=True)`

Return accounts linked to ``user`` ordered by name.

### `list_users_for_account(account, active_only=True)`

Return users linked to ``account`` ordered by username.

### `require_account_member(user, account)`

Raise PermissionDenied unless ``user`` has an active membership on ``account``.

### `search_users(term, limit=20)`

Staff helper: find CustomUsers by username, name, or email (case-insensitive).

### `set_active_account(request, account_id)`

Set session active account after validating active membership.

Returns the Account. Raises PermissionDenied if the user is not an active member.

## `boxes.backend.pickup`

Pickup day availability: schedule expansion and open-day windows.

### `enqueue_pickup_cancellation_emails(pickup_day: 'PickupDay') -> 'int'`

Enqueue EmailQueue rows for reserved packages when a day is cancelled.

Looks up template named "Pickup Day Cancelled". If missing, logs and
returns 0. Returns number of queue rows created.

### `expand_schedule_rule(rule: 'PickupScheduleRule', window_start: 'date', window_end: 'date') -> 'set[date]'`

Return dates generated by a single rule inside [window_start, window_end].

Inactive rules yield nothing. Window is inclusive on both ends.

### `expand_schedule_rules(window_start: 'date', window_end: 'date', rules: 'Optional[Iterable[PickupScheduleRule]]' = None) -> 'set[date]'`

Union of dates from active schedule rules in the inclusive window.

### `get_or_create_open_pickup_day(target: 'date') -> 'PickupDay'`

Return an active PickupDay for target if that date is open.

Raises ValueError when the date is not an open pickup day.

### `list_open_pickup_dates(window_start: 'date', window_end: 'date', rules: 'Optional[Iterable[PickupScheduleRule]]' = None) -> 'list[date]'`

Open pickup dates in [window_start, window_end], sorted ascending.

Candidates come from schedule rules plus explicit active PickupDay rows.
Any PickupDay with is_active=False is removed (inactive override).

### `list_open_pickup_days(window_start: 'date', window_end: 'date', rules: 'Optional[Iterable[PickupScheduleRule]]' = None, ensure_rows: 'bool' = False) -> 'list[PickupDay]'`

Return persisted PickupDay rows for open dates in the window.

With ensure_rows=True, missing open dates are created as active days.
Without it, only dates that already have a PickupDay row are returned.

### `set_pickup_day_active(pickup_day: 'PickupDay', is_active: 'bool') -> 'PickupDay'`

Set is_active on a day; when deactivating with reservations, notify.

## `boxes.backend.reports`

Report query building, config cleaning, and chart data generation.

### `clean_config(config)`

Normalize and validate a report config dict from the UI.

### `generate_full_report(pk)`

Execute report ``pk`` config against the ORM and return tabular result data.

### `packages_by_carrier_by_day(timeframe_filter)`

Group PackageLedger check-ins by carrier name and calendar day.

Returns ``{"x_data": [...], "y_data": {carrier: [counts...]}}`` for charting.

### `report_chart_generate(timeframe_filter)`

Build chart series data for the given timeframe filter.

## `boxes.backend.signup`

Signup invite creation, email delivery, and token-gated registration.

### `complete_signup(*, token, username, password, password2=None, first_name=None, last_name=None, company=None, phone_number=None, mobile_number=None)`

Create an active portal user from a valid invite token.

Returns dict with user, invite, membership (optional). Raises ValidationError
on bad token or form data.

### `create_signup_invite(*, email, actor=None, first_name='', last_name='', middle_name='', prefix='', suffix='', company='', phone_number='', mobile_number='', account=None, role='owner', create_account=False, account_name=None, billable=True, comments=None, expires_days=14)`

Create a SignupInvite (and optionally a billing Account to link on accept).

Does **not** create a CustomUser — the invitee registers via the signed link.
Returns the SignupInvite instance.

### `get_valid_invite(token)`

Return a usable SignupInvite or raise ValidationError.

### `invite_signup_url(invite, request=None)`

Absolute (when request given) or path-only signup URL for ``invite``.

### `send_signup_invite_email(invite, request=None)`

Deliver the invite email. Returns True if a provider accepted the message.

Honors GlobalSettings.email_sending. Tries Mailjet first, then Django
``send_mail``. Updates ``email_sent_at`` / ``last_error`` on the invite.

## `boxes.backend.system`

Helpers for automated actors and singleton configuration rows.

### `ensure_system_user()`

Create the inactive ``system`` user if it does not exist yet.

### `get_system_user()`

Return the CustomUser used for automated ledger and system actions.

Prefers an inactive user named ``system``. Falls back to the earliest
superuser, then the earliest user by primary key. Creates the system
user when the database has no users yet (migrations / empty installs).

### `get_system_user_pk()`

Primary key of the system user (for on_delete=SET callables).
