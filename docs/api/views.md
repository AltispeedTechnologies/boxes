# Views (generated)

Public callables discovered under `boxes.views`.

## `boxes.views`

Auto-import top-level view modules.

## `boxes.views.account`

Staff account detail: search, ledger, packages, emails, updates.

### `account_edit(request, pk)`

Render staff account edit page.

### `account_emails(request, pk)`

List sent emails related to an account.

### `account_ledger(request, pk)`

Render or return ledger rows for an account.

### `account_packages(request, pk)`

List packages belonging to an account.

### `account_search(request)`

JSON/Select2 search over accounts and aliases.

### `update_account(request, pk)`

POST: update account fields (name, billable, comments, etc.).

### `update_account_aliases(request)`

POST: replace/update account alias list.

## `boxes.views.auth`

Session login and logout views.

### `sign_in(request)`

Render login form or authenticate and redirect (honors ``next``).

### `sign_out(request)`

Log out the current user and redirect to login.

## `boxes.views.carrier`

Carrier search endpoint for Select2.

### `carrier_search(request)`

GET: search carriers by name.

## `boxes.views.common`

Shared helpers for package/email querysets used by multiple views.

## `boxes.views.customer`

Customer portal: parcels, payments, invoices, billing portal.

### `customer_billing_portal(request)`

GET: redirect to Stripe Billing Portal session.

### `customer_cancel_invoice(request, pk)`

GET: cancel an open invoice/PaymentIntent.

### `customer_confirm_invoice(request, pk)`

POST: confirm and finalize payment for invoice.

### `customer_make_payment(request)`

GET: payment page with balance and methods.

### `customer_new_invoice(request)`

POST: create invoice/PaymentIntent for amount and method.

### `customer_parcels(request)`

GET: customer's package list for linked account.

### `customer_payment_methods(request)`

GET: payment methods data for UI.

### `customer_view_invoice(request, pk)`

GET: invoice detail / confirmation page.

### `customer_view_pdf(request, pk)`

GET: invoice PDF download/view.

## `boxes.views.emails`

Staff email content inspection.

### `get_email_contents(request, pk)`

GET: return HTML body for a SentEmail primary key.

## `boxes.views.index`

Customer home page.

### `index(request)`

Render customer landing page.

## `boxes.views.labels`

ReportLab package label generation.

### `draw_label(canvas, first_name, last_name, barcode_value, date, inside)`

Draw one label onto a ReportLab canvas.

### `generate_label(request)`

GET: stream multi-label PDF for requested packages.

### `get_ids(request)`

Parse package ids from the request for label printing.

### `show_label(request)`

GET: label print UI.

## `boxes.views.mgmt`

Auto-import management settings views.

## `boxes.views.mgmt.accounts`

Staff account list management page.

### `account_mgmt(request)`

GET: management accounts list/search UI.

## `boxes.views.mgmt.carriers`

Carrier catalog management.

### `carrier_settings(request)`

GET: carriers management page.

### `update_carriers(request)`

POST: create/update/delete carriers from form data.

## `boxes.views.mgmt.charges`

Aging charge rules and tax settings UI.

### `charge_settings(request)`

GET: charges and tax configuration page.

### `get_tax_rate(tax_rate)`

Ensure a Stripe Tax Rate exists for ``tax_rate``; return id.

### `save_charge_settings(request)`

POST: persist AccountChargeSettings and tax GlobalSettings fields.

## `boxes.views.mgmt.email`

Email settings and logs management.

### `email_logs(request)`

GET: sent email log listing.

### `email_settings(request)`

GET: sender and notification rules page.

### `save_email_settings(request)`

POST: save EmailSettings and NotificationRule rows.

## `boxes.views.mgmt.email_templates`

Email template CRUD for staff.

### `add_email_template(request)`

POST: create a new EmailTemplate.

### `email_template(request)`

GET: template list/editor page.

### `email_template_content(request)`

GET: fetch subject/body for a template id.

### `update_email_template(request)`

POST: update template name/subject/content.

## `boxes.views.mgmt.general`

GlobalSettings (business identity and logos) management.

### `general_settings(request)`

GET: general settings page.

### `resize_and_save(image, size, format, model, attribute, filename)`

Resize an image and assign it to a model ImageField attribute.

### `save_general_settings(request)`

POST: save GlobalSettings fields and process logo upload.

## `boxes.views.mgmt.types`

Package type catalog management.

### `package_type_settings(request)`

GET: package types management page.

### `update_package_types(request)`

POST: create/update/delete package types.

## `boxes.views.modals`

HTML modal partial endpoints for package UI.

### `get_actions_modals(request)`

Return row-action modal markup.

### `get_bulk_modals(request)`

Return bulk-action modal markup.

### `get_picklist_mgmt_modals(request)`

Return picklist management modal markup.

## `boxes.views.packages`

Auto-import package view modules.

## `boxes.views.packages.backend`

Package-adjacent JSON helpers (types, queues).

### `queue_packages(request, pk)`

GET: packages currently in queue ``pk``.

### `type_search(request)`

GET: PackageType Select2 search.

### `update_queue_name(request, pk)`

POST: rename a queue.

## `boxes.views.packages.check_in`

Package check-in UI and creation.

### `check_in(request)`

GET: check-in page with queue selector.

### `check_in_packages(request)`

POST: transition selected packages to checked-in state.

### `create_package(request)`

POST: create a package (and queue membership) from form data.

## `boxes.views.packages.check_out`

Package check-out UI and state transitions.

### `check_out(request)`

GET: check-out page.

### `check_out_packages(request)`

POST: check out packages (state → Checked out).

### `check_out_packages_reverse(request)`

POST: reverse a check-out back to checked-in.

### `verify_can_checkout(request)`

POST: validate packages can be checked out (paid/balance rules).

## `boxes.views.packages.package`

Single-package detail and update endpoints.

### `package_detail(request, pk)`

GET: package detail page with history.

### `update_package(request, pk)`

POST: update fields on one package.

### `update_packages(request)`

POST: bulk update package fields.

## `boxes.views.packages.search`

Package listing and search pages.

### `all_packages(request)`

GET: all-packages listing.

### `search_packages(request)`

GET: search packages by query/filters.

## `boxes.views.packages.utility`

Shared package field update and state-transition utilities.

### `update_packages_fields(package_ids, package_data, user, no_ledger=False)`

Apply field changes to package ids; optional ledger suppression.

### `update_packages_util(request, state, debit_credit_switch=False)`

Parse request and apply a target state with debit/credit switch.

## `boxes.views.picklists`

Staff picklist CRUD, assignment, and checkout.

### `create_picklist(request)`

POST: create a picklist (date/description).

### `modify_package_picklist(request)`

POST: assign packages to a picklist.

### `picklist_check_out(request, pk=None)`

GET: checkout flow scoped to a picklist.

### `picklist_list(request, pk=None)`

GET: picklist index page.

### `picklist_query(request)`

GET: query picklists for UI widgets.

### `picklist_show(request, pk=None)`

GET: picklist detail page.

### `picklist_show_table(request, pk=None)`

GET: packages table fragment for a picklist.

### `remove_package_picklist(request)`

POST: remove packages from picklists.

### `remove_picklist(request, pk)`

POST: delete a picklist by id.

## `boxes.views.reports`

Auto-import report view modules.

## `boxes.views.reports.backend`

Report mutation and chart JSON endpoints.

### `report_generate_pdf(request, pk)`

Queue or trigger PDF generation for report ``pk``.

### `report_name_search(request)`

POST: check report name availability/search.

### `report_new_submit(request)`

POST: create a new Report from config JSON.

### `report_remove(request, pk)`

POST: delete report ``pk``.

### `report_stats_chart(request)`

POST: return chart data payload for dashboard.

### `report_update(request, pk)`

POST: update report ``pk`` config.

## `boxes.views.reports.frontend`

Report HTML pages and export downloads.

### `report_data(request)`

GET: dashboard data page shell.

### `report_data_view(request)`

GET: data/chart fragment for frequency tabs.

### `report_details(request, pk=None)`

GET: create/edit report builder UI.

### `report_list(request)`

GET: list saved reports.

### `report_view(request, pk)`

GET: view report results and generation status.

### `report_view_csv(request, pk)`

GET: stream report as CSV.

### `report_view_pdf(request, pk)`

GET: serve generated PDF if available.

## `boxes.views.user`

Profile self-service and staff user create/update endpoints.

### `create_user(request)`

POST (staff): create user, optional account link, set groups.

### `generate_username()`

Generate a unique username string for new users.

### `profile_user(request)`

Self-service profile for the logged-in CustomUser.

CustomUser is the login identity. Account is a separate billing/parcel
entity linked through UserAccount. Profile edits only touch the user
(and notification emails). If the user is linked to exactly one Account,
name changes are mirrored onto that account's display name / primary
alias — the same rule staff edit uses.

### `update_profile(request)`

Update the authenticated user's profile fields (and optional password).

### `update_profile_emails(request)`

Create/update/remove CustomUserEmail rows for the authenticated user only.

### `update_user(request)`

POST (staff): update a target user's profile fields.

### `update_user_emails(request)`

POST (staff): update notification emails for a target user.

## `boxes.views.webhooks`

External webhook receivers.

### `stripe_webhooks(request)`

POST: verify Stripe signature and enqueue payment handling.
