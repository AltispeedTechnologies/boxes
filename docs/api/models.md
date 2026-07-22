# Models (generated)

Introspected from the Django app registry (`boxes` models only).

## Account

`boxes.Account` — db table `boxes_account`

Billing and parcel entity for a customer.

``user`` is the creator/owner (often staff), **not** the customer portal link — use ``UserAccount`` for that. Balance sign: negative typically means amount owed.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `accountbalance` | OneToOneField | True |  | boxes.AccountBalance |  |
| `accountledger` | ForeignKey | True |  | boxes.AccountLedger |  |
| `user_memberships` | ForeignKey | True |  | boxes.UserAccount |  |
| `accountalias` | ForeignKey | True |  | boxes.AccountAlias |  |
| `accountstripecustomer` | ForeignKey | True |  | boxes.AccountStripeCustomer |  |
| `invoice` | ForeignKey | True |  | boxes.Invoice |  |
| `sentemail` | ForeignKey | True |  | boxes.SentEmail |  |
| `package` | ForeignKey | True |  | boxes.Package |  |
| `signup_invites` | ForeignKey | True |  | boxes.SignupInvite |  |
| `id` | BigAutoField | False |  |  |  |
| `user` | ForeignKey | False |  | boxes.CustomUser |  |
| `name` | CharField | False |  |  |  |
| `balance` | DecimalField | False |  |  |  |
| `billable` | BooleanField | False |  |  |  |
| `comments` | CharField | True |  |  |  |

**Methods**

- `amount_owed(self)` — Customer liability as a non-negative Decimal (0 if credit or zero).
- `display_balance_amount(self)` — Absolute magnitude of balance for dollar formatting (always >= 0).
- `ensure_primary_alias(self)` — Create or update the primary ``AccountAlias`` to match ``name``.
- `hr_balance(self)` — Return a human-readable absolute dollar string for ``balance``.

## AccountAlias

`boxes.AccountAlias` — db table `boxes_accountalias`

Searchable alternate name for an account; one row may be ``primary``.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `account` | ForeignKey | False |  | boxes.Account |  |
| `alias` | CharField | False |  |  |  |
| `primary` | BooleanField | False |  |  |  |

## AccountBalance

`boxes.AccountBalance` — db table `boxes_accountbalance`

Denormalized regular vs late balances for an account (1:1).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `account` | OneToOneField | False |  | boxes.Account |  |
| `regular_balance` | DecimalField | False |  |  |  |
| `late_balance` | DecimalField | False |  |  |  |

**Methods**

- `hr_late_balance(self)` — Human-readable late balance string.
- `hr_regular_balance(self)` — Human-readable regular balance string.

## AccountChargeSettings

`boxes.AccountChargeSettings` — db table `boxes_accountchargesettings`

Aging/storage fee rule applied by Celery ``age_charges``.

Frequency codes: ``D`` daily, ``W`` weekly, ``M`` monthly.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `days` | IntegerField | True |  |  |  |
| `price` | DecimalField | True |  |  |  |
| `package_type` | ForeignKey | True |  | boxes.PackageType |  |
| `frequency` | CharField | True |  |  |  |
| `endpoint` | IntegerField | True |  |  |  |

## AccountLedger

`boxes.AccountLedger` — db table `boxes_accountledger`

Single financial movement (credit/debit) optionally tied to package or invoice.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `user` | ForeignKey | False |  | boxes.CustomUser |  |
| `account` | ForeignKey | False |  | boxes.Account |  |
| `credit` | DecimalField | False |  |  |  |
| `debit` | DecimalField | False |  |  |  |
| `timestamp` | DateTimeField | False | (callable) |  |  |
| `description` | CharField | True |  |  |  |
| `package` | ForeignKey | True |  | boxes.Package |  |
| `invoice` | ForeignKey | True |  | boxes.Invoice |  |
| `is_late` | BooleanField | False |  |  |  |

## AccountStripeCustomer

`boxes.AccountStripeCustomer` — db table `boxes_accountstripecustomer`

Stripe Customer id associated with an Account.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `stripepaymentmethod` | ForeignKey | True |  | boxes.StripePaymentMethod |  |
| `id` | BigAutoField | False |  |  |  |
| `account` | ForeignKey | False |  | boxes.Account |  |
| `customer_id` | CharField | True |  |  |  |

## Carrier

`boxes.Carrier` — db table `boxes_carrier`

Shipping carrier (name, phone, website) selectable on packages.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `package` | ForeignKey | True |  | boxes.Package |  |
| `id` | BigAutoField | False |  |  |  |
| `name` | CharField | False |  |  |  |
| `phone_number` | CharField | False |  |  |  |
| `website` | CharField | False |  |  |  |
| `is_active` | BooleanField | False | True |  |  |
| `allow_duplicate_tracking` | BooleanField | False | False |  |  |

## Chart

`boxes.Chart` — db table `boxes_chart`

Cached chart series for a frequency window (Today/Week/Month/Quarter/Year).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `frequency` | CharField | False |  |  |  |
| `last_updated` | DateTimeField | False |  |  |  |
| `chart_data` | JSONField | True |  |  |  |
| `total_data` | JSONField | False |  |  |  |

## CustomUser

`boxes.CustomUser` — db table `boxes_customuser`

Application user model (``AUTH_USER_MODEL``).

Extends Django ``AbstractUser`` with warehouse profile fields. Role checks use **group membership** methods rather than only boolean flags.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `logentry` | ForeignKey | True |  | admin.LogEntry |  |
| `account` | ForeignKey | True |  | boxes.Account |  |
| `accountledger` | ForeignKey | True |  | boxes.AccountLedger |  |
| `account_memberships` | ForeignKey | True |  | boxes.UserAccount |  |
| `invoice` | ForeignKey | True |  | boxes.Invoice |  |
| `packageledger` | ForeignKey | True |  | boxes.PackageLedger |  |
| `pickup_reservations` | ForeignKey | True |  | boxes.PackagePickupReservation |  |
| `customuseremail` | ForeignKey | True |  | boxes.CustomUserEmail |  |
| `sent_signup_invites` | ForeignKey | True |  | boxes.SignupInvite |  |
| `accepted_signup_invites` | ForeignKey | True |  | boxes.SignupInvite |  |
| `id` | BigAutoField | False |  |  |  |
| `password` | CharField | False |  |  |  |
| `last_login` | DateTimeField | True |  |  |  |
| `is_superuser` | BooleanField | False | False |  | Designates that this user has all permissions without explicitly assigning them. |
| `username` | CharField | False |  |  | Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. |
| `first_name` | CharField | False |  |  |  |
| `last_name` | CharField | False |  |  |  |
| `email` | CharField | False |  |  |  |
| `is_staff` | BooleanField | False | False |  | Designates whether the user can log into this admin site. |
| `is_active` | BooleanField | False | True |  | Designates whether this user should be treated as active. Unselect this instead of deleting accounts. |
| `date_joined` | DateTimeField | False | (callable) |  |  |
| `company` | CharField | True |  |  |  |
| `phone_number` | CharField | True |  |  |  |
| `mobile_number` | CharField | True |  |  |  |
| `prefix` | CharField | True |  |  |  |
| `middle_name` | CharField | True |  |  |  |
| `suffix` | CharField | True |  |  |  |
| `comments` | CharField | True |  |  |  |
| `groups` | ManyToManyField | False |  | auth.Group |  |
| `user_permissions` | ManyToManyField | False |  | auth.Permission |  |

**Methods**

- `has_delivery_role(self)` — True if the user is in the Delivery group.
- `has_staff_role(self)` — True if the user is in the Staff group.
- `is_admin(self)` — Return True if the user is in the Admin group.
- `is_customer(self)` — Return True if the user is in the Customer group.

## CustomUserEmail

`boxes.CustomUserEmail` — db table `boxes_customuseremail`

Notification email address for a login (Mailjet recipients).

Distinct from ``AbstractUser.email``; users may have multiple notification addresses.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `user` | ForeignKey | False |  | boxes.CustomUser |  |
| `email` | CharField | False |  |  |  |

## EmailQueue

`boxes.EmailQueue` — db table `boxes_emailqueue`

Pending outbound email work item (package + template).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `package` | ForeignKey | False |  | boxes.Package |  |
| `template` | ForeignKey | False |  | boxes.EmailTemplate |  |

## EmailSettings

`boxes.EmailSettings` — db table `boxes_emailsettings`

Sender identity and default check-in template (singleton-style).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `notification_rules` | ForeignKey | True |  | boxes.NotificationRule |  |
| `id` | BigAutoField | False |  |  |  |
| `sender_name` | CharField | False |  |  |  |
| `sender_email` | CharField | False |  |  |  |
| `check_in_template` | ForeignKey | True |  | boxes.EmailTemplate |  |

## EmailTemplate

`boxes.EmailTemplate` — db table `boxes_emailtemplate`

Reusable subject/body template for notifications.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `check_in_templates` | ForeignKey | True |  | boxes.EmailSettings |  |
| `notificationrule` | ForeignKey | True |  | boxes.NotificationRule |  |
| `emailqueue` | ForeignKey | True |  | boxes.EmailQueue |  |
| `id` | BigAutoField | False |  |  |  |
| `name` | CharField | False |  |  |  |
| `subject` | CharField | False |  |  |  |
| `content` | TextField | False |  |  |  |

## GlobalSettings

`boxes.GlobalSettings` — db table `boxes_globalsettings`

Warehouse identity, tax/fee toggles, email master switch, and logos.

Prefer GlobalSettings.load() over hard-coded primary keys. Edited via
Management -> General. See docs/DATABASE_SETTINGS.md.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `name` | CharField | False |  |  |  |
| `address1` | CharField | False |  |  |  |
| `address2` | CharField | False |  |  |  |
| `website` | CharField | False |  |  |  |
| `email` | CharField | False |  |  |  |
| `phone_number` | CharField | True |  |  |  |
| `email_sending` | BooleanField | False | True |  |  |
| `taxes` | BooleanField | False | False |  |  |
| `tax_rate` | DecimalField | True |  |  |  |
| `tax_stripe_id` | CharField | True |  |  |  |
| `pass_on_fees` | BooleanField | False | False |  |  |
| `source_image` | FileField | False |  |  |  |
| `login_image` | FileField | False |  |  |  |
| `label_image` | FileField | False |  |  |  |
| `navbar_image` | FileField | False |  |  |  |
| `favicon_image` | FileField | False |  |  |  |

## Invoice

`boxes.Invoice` — db table `boxes_invoice`

Payment record with line items JSON and PaymentIntent state machine.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `accountledger` | ForeignKey | True |  | boxes.AccountLedger |  |
| `id` | BigAutoField | False |  |  |  |
| `account` | ForeignKey | False |  | boxes.Account |  |
| `user` | ForeignKey | False |  | boxes.CustomUser |  |
| `timestamp` | DateTimeField | False |  |  |  |
| `payment_intent_id` | CharField | True |  |  |  |
| `current_state` | PositiveSmallIntegerField | False | 0 |  |  |
| `line_items` | JSONField | False |  |  |  |
| `subtotal` | DecimalField | False |  |  |  |
| `tax` | DecimalField | True |  |  |  |
| `processing_fees` | DecimalField | True |  |  |  |
| `stripe_fee` | DecimalField | True |  |  |  |
| `deposit_total` | DecimalField | True |  |  |  |

## NotificationRule

`boxes.NotificationRule` — db table `boxes_notificationrule`

After ``days`` days, enqueue ``template`` for matching packages.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `email_settings` | ForeignKey | False |  | boxes.EmailSettings |  |
| `days` | IntegerField | False |  |  |  |
| `template` | ForeignKey | False |  | boxes.EmailTemplate |  |

## Package

`boxes.Package` — db table `boxes_package`

A physical parcel tracked through warehouse states.

States: 0 Received, 1 Checked in, 2 Checked out, 3 Mis-placed. FKs to Account/Carrier/PackageType use RESTRICT.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `accountledger` | ForeignKey | True |  | boxes.AccountLedger |  |
| `emailqueue` | ForeignKey | True |  | boxes.EmailQueue |  |
| `sentemailpackage` | ForeignKey | True |  | boxes.SentEmailPackage |  |
| `packageledger` | ForeignKey | True |  | boxes.PackageLedger |  |
| `pickup_reservation` | OneToOneField | True |  | boxes.PackagePickupReservation |  |
| `packagequeue` | OneToOneField | True |  | boxes.PackageQueue |  |
| `packagepicklist` | OneToOneField | True |  | boxes.PackagePicklist |  |
| `id` | BigAutoField | False |  |  |  |
| `account` | ForeignKey | False |  | boxes.Account |  |
| `carrier` | ForeignKey | False |  | boxes.Carrier |  |
| `package_type` | ForeignKey | False |  | boxes.PackageType |  |
| `inside` | BooleanField | False | False |  |  |
| `tracking_code` | CharField | False |  |  |  |
| `current_state` | PositiveSmallIntegerField | False | 0 |  |  |
| `price` | DecimalField | False |  |  |  |
| `comments` | CharField | True |  |  |  |
| `paid` | BooleanField | False | False |  |  |

## PackageLedger

`boxes.PackageLedger` — db table `boxes_packageledger`

Historical record of a package state transition by a user.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `user` | ForeignKey | False |  | boxes.CustomUser |  |
| `package` | ForeignKey | False |  | boxes.Package |  |
| `state` | PositiveSmallIntegerField | False |  |  |  |
| `timestamp` | DateTimeField | False |  |  |  |

## PackagePicklist

`boxes.PackagePicklist` — db table `boxes_packagepicklist`

Membership of a package on a picklist (one picklist per package).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `package` | OneToOneField | False |  | boxes.Package |  |
| `picklist` | ForeignKey | False |  | boxes.Picklist |  |

## PackagePickupReservation

`boxes.PackagePickupReservation` — db table `boxes_packagepickupreservation`

Customer reservation of a package for a specific pickup day.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `package` | OneToOneField | False |  | boxes.Package |  |
| `pickup_day` | ForeignKey | False |  | boxes.PickupDay |  |
| `user` | ForeignKey | False |  | boxes.CustomUser |  |
| `created_at` | DateTimeField | False |  |  |  |

## PackageQueue

`boxes.PackageQueue` — db table `boxes_packagequeue`

Places a package into a queue (one queue membership per package).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `package` | OneToOneField | False |  | boxes.Package |  |
| `queue` | ForeignKey | False |  | boxes.Queue |  |

## PackageSystemTrackingCode

`boxes.PackageSystemTrackingCode` — db table `boxes_packagesystemtrackingcode`

Counter used to mint internal tracking codes (prefix + last_number).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `prefix` | CharField | False | 'INT' |  |  |
| `last_number` | IntegerField | False | 0 |  |  |

## PackageType

`boxes.PackageType` — db table `boxes_packagetype`

Classification of a parcel (shortcode, description, default price).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `accountchargesettings` | ForeignKey | True |  | boxes.AccountChargeSettings |  |
| `package` | ForeignKey | True |  | boxes.Package |  |
| `id` | BigAutoField | False |  |  |  |
| `shortcode` | CharField | False |  |  |  |
| `description` | CharField | False |  |  |  |
| `default_price` | DecimalField | False |  |  |  |
| `is_active` | BooleanField | False | True |  |  |

## Picklist

`boxes.Picklist` — db table `boxes_picklist`

A named/dated list of packages to pull for pickup.

Requires at least one of ``date`` or ``description``.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `pickup_days` | ForeignKey | True |  | boxes.PickupDay |  |
| `picklistqueue` | OneToOneField | True |  | boxes.PicklistQueue |  |
| `packagepicklist` | ForeignKey | True |  | boxes.PackagePicklist |  |
| `id` | BigAutoField | False |  |  |  |
| `date` | DateField | True |  |  |  |
| `description` | TextField | True |  |  |  |

**Methods**

- `clean(self)` — Validate that date or description is present.
- `save(self, *args, **kwargs)` — Run validation then save.

## PicklistQueue

`boxes.PicklistQueue` — db table `boxes_picklistqueue`

Associates a picklist with a queue (one-to-one each side).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `picklist` | OneToOneField | False |  | boxes.Picklist |  |
| `queue` | OneToOneField | False |  | boxes.Queue |  |

## PickupDay

`boxes.PickupDay` — db table `boxes_pickupday`

A concrete calendar day available (or disabled) for customer pickup.

is_active=False overrides a schedule rule so the day is closed even if
a weekly rule would otherwise open it. Optional link to a staff Picklist.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `reservations` | ForeignKey | True |  | boxes.PackagePickupReservation |  |
| `id` | BigAutoField | False |  |  |  |
| `date` | DateField | False |  |  |  |
| `picklist` | ForeignKey | True |  | boxes.Picklist |  |
| `is_active` | BooleanField | False | True |  |  |
| `notes` | TextField | True |  |  |  |

## PickupScheduleRule

`boxes.PickupScheduleRule` — db table `boxes_pickupschedulerule`

Rule that generates open pickup days in a date window.

recurrence:
  - none: a single day on start_date (weekday ignored)
  - weekly: every weekday from start_date through end_date (if set)
weekday uses Python date.weekday() (0=Monday through 6=Sunday).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `name` | CharField | False |  |  |  |
| `recurrence` | CharField | False | 'none' |  |  |
| `weekday` | PositiveSmallIntegerField | True |  |  |  |
| `start_date` | DateField | False |  |  |  |
| `end_date` | DateField | True |  |  |  |
| `is_active` | BooleanField | False | True |  |  |

## Queue

`boxes.Queue` — db table `boxes_queue`

Named staging queue; ``check_in`` marks check-in line queues.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `packagequeue` | ForeignKey | True |  | boxes.PackageQueue |  |
| `picklistqueue` | OneToOneField | True |  | boxes.PicklistQueue |  |
| `id` | BigAutoField | False |  |  |  |
| `description` | TextField | False |  |  |  |
| `check_in` | BooleanField | False |  |  |  |

## Report

`boxes.Report` — db table `boxes_report`

Named report definition; ``config`` holds field/filter JSON.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `reportresult` | OneToOneField | True |  | boxes.ReportResult |  |
| `id` | BigAutoField | False |  |  |  |
| `name` | CharField | False |  |  |  |
| `config` | JSONField | False |  |  |  |

## ReportResult

`boxes.ReportResult` — db table `boxes_reportresult`

Generation status, progress, and PDF path for a report (1:1).

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `report` | OneToOneField | False |  | boxes.Report |  |
| `pdf_path` | CharField | True |  |  |  |
| `last_success` | DateTimeField | True |  |  |  |
| `status` | IntegerField | False | 0 |  |  |
| `progress` | IntegerField | False | 0 |  |  |

## SentEmail

`boxes.SentEmail` — db table `boxes_sentemail`

Audit row for an attempted send (success, Mailjet uuid, recipient).

``account`` is set for package notifications; signup invites may omit it
when no billing account is linked yet.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `sentemailcontents` | ForeignKey | True |  | boxes.SentEmailContents |  |
| `sentemailpackage` | ForeignKey | True |  | boxes.SentEmailPackage |  |
| `sentemailresult` | ForeignKey | True |  | boxes.SentEmailResult |  |
| `events` | ForeignKey | True |  | boxes.SentEmailEvent |  |
| `id` | BigAutoField | False |  |  |  |
| `account` | ForeignKey | True |  | boxes.Account |  |
| `subject` | CharField | False |  |  |  |
| `email` | CharField | False |  |  |  |
| `timestamp` | DateTimeField | False | (callable) |  |  |
| `success` | BooleanField | False |  |  |  |
| `message_uuid` | CharField | True |  |  |  |

## SentEmailContents

`boxes.SentEmailContents` — db table `boxes_sentemailcontents`

HTML body snapshot for a sent email.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `sent_email` | ForeignKey | False |  | boxes.SentEmail |  |
| `html` | TextField | False |  |  |  |

## SentEmailEvent

`boxes.SentEmailEvent` — db table `boxes_sentemailevent`

Mailjet delivery event (sent/open/click/bounce/etc.) for a sent message.

Linked to SentEmail when Message_GUID matches ``message_uuid``; unmatched
events are still stored for later reconciliation.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `sent_email` | ForeignKey | True |  | boxes.SentEmail |  |
| `event_type` | CharField | False |  |  |  |
| `timestamp` | DateTimeField | False |  |  |  |
| `message_uuid` | CharField | True |  |  |  |
| `email` | CharField | True |  |  |  |
| `payload` | JSONField | True |  |  |  |

## SentEmailPackage

`boxes.SentEmailPackage` — db table `boxes_sentemailpackage`

Packages referenced by a sent email.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `sent_email` | ForeignKey | False |  | boxes.SentEmail |  |
| `package` | ForeignKey | False |  | boxes.Package |  |

## SentEmailResult

`boxes.SentEmailResult` — db table `boxes_sentemailresult`

Raw provider response JSON for a send attempt.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `sent_email` | ForeignKey | False |  | boxes.SentEmail |  |
| `response` | JSONField | False |  |  |  |

## SignupInvite

`boxes.SignupInvite` — db table `boxes_signupinvite`

One-time sign-up invitation. Registration is only allowed via a valid token.

Staff create invites (and optionally a billing Account to link on accept).
Customers complete registration at ``/signup/<token>/`` only — there is no
open public registration endpoint.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `token` | CharField | False | (callable) |  |  |
| `email` | CharField | False |  |  |  |
| `first_name` | CharField | False | '' |  |  |
| `last_name` | CharField | False | '' |  |  |
| `middle_name` | CharField | False | '' |  |  |
| `prefix` | CharField | False | '' |  |  |
| `suffix` | CharField | False | '' |  |  |
| `company` | CharField | False | '' |  |  |
| `phone_number` | CharField | False | '' |  |  |
| `mobile_number` | CharField | False | '' |  |  |
| `account` | ForeignKey | True |  | boxes.Account |  |
| `role` | CharField | False | 'owner' |  |  |
| `created_by` | ForeignKey | True |  | boxes.CustomUser |  |
| `created_at` | DateTimeField | False | (callable) |  |  |
| `expires_at` | DateTimeField | False | (callable) |  |  |
| `used_at` | DateTimeField | True |  |  |  |
| `used_by` | ForeignKey | True |  | boxes.CustomUser |  |
| `email_sent_at` | DateTimeField | True |  |  |  |
| `last_error` | CharField | False | '' |  |  |

**Methods**

- `is_expired(self)` — True if past expires_at.
- `is_usable(self)` — True if not used and not expired.

## StripePaymentMethod

`boxes.StripePaymentMethod` — db table `boxes_stripepaymentmethod`

Cached Stripe payment method id for a customer.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `customer` | ForeignKey | False |  | boxes.AccountStripeCustomer |  |
| `payment_method_id` | CharField | False |  |  |  |

## UserAccount

`boxes.UserAccount` — db table `boxes_useraccount`

Join table linking a login (CustomUser) to a billing Account for portal access.

| Field | Type | Null | Default | Related | Help |
|-------|------|------|---------|---------|------|
| `id` | BigAutoField | False |  |  |  |
| `user` | ForeignKey | False |  | boxes.CustomUser |  |
| `account` | ForeignKey | False |  | boxes.Account |  |
| `is_active` | BooleanField | False | True |  |  |
| `role` | CharField | False | 'member' |  |  |
| `created_at` | DateTimeField | True |  |  |  |
