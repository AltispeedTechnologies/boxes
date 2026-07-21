# JavaScript (generated)

Parsed from `boxes/static/js` file headers and `function` declarations.

## `account.js`

@file account.js; @description Staff account detail page interactions (comments, membership, web accounts, fee waiver).; @see docs/api/javascript.md

- `function init_account_page()`

## `app.js`

@file app.js; @description Global AJAX helpers, CSRF, Select2 utilities, debounce,;              BoxesPage mount/unmount registry, and htmx app-shell hooks.; @see docs/api/javascript.md; htmx shell notes; ----------------; base.html boosts links/forms inside #app-main only (navbar stays mounted).; Page scripts in {% block javascript %} load on FULL document navigation.; On boosted navigations the head is not re-parsed, so:;   - Prefer BoxesPage.register("page-id", { mount, unmount });   - Set data-page / {% block page_id %} so afterSettle can remount;   - unmount should tear down listeners/widgets the module owns; Do not reintroduce Turbo.

- `function init_page()` — Document-ready / afterSettle bootstrap for shared UI widgets. Safe to call on full load and after every htmx settle of #app-main.
- `function update_navbar_active()` — Highlight navbar links from the current path (navbar is outside hx-boost).
- `function ensure_auth_chrome()` — If htmx swapped main after login/logout without refreshing the navbar, force a full document load so auth chrome matches session state.
- `function boot_app_main()`
- `window.get_cookie = function(...)`
- `window.select2properheight = function(...)`
- `window.initialize_async_select2 = function(...)`
- `window.display_error_message = function(...)`
- `window.debounce = function(...)`
- `window.format_price_input = function(...)`
- `window.ajax_request = function(...)`

## `bulk_actions.js`

@file bulk_actions.js; @description Bulk package field updates from multi-select tables.; @see docs/api/javascript.md

- `function update_package_rows()`
- `function setup_bulk_actions()` — Bind bulk action controls on package tables.

## `check_out.js`

@file check_out.js; @description Check-out page initialization and submit wiring.; @see docs/api/javascript.md

- `function init_checkout_page()`

## `check_out_box.js`

@file check_out_box.js; @description Per-package checkout verification UI before submit.; @see docs/api/javascript.md

- `function verify_package()`
- `function setup_checkout_box()` — Bind checkout verification box events.

## `create.js`

@file create.js; @description Check-in page: create package, queue load, and check-in submit.; @see docs/api/javascript.md

- `function request_create_package()`
- `function handle_create_package()` — Collect form fields and create a package row.
- `function reset_form_fields()` — Clear the create-package form.
- `function display_packages()` — Render created/queued packages into the check-in table.
- `function handle_checkin()` — Submit check-in for visible table packages.
- `function load_queue()` — Load packages for the selected queue into the table.
- `function init_create_page()` — Initialize check-in/create page handlers.

## `customer/billing_portal.js`

@file customer/billing_portal.js; @description Stripe Billing Portal redirect helpers.; @see docs/api/javascript.md


## `customer/confirm_payment.js`

@file customer/confirm_payment.js; @description Invoice confirmation and client-side payment completion.; @see docs/api/javascript.md

- `function init_invoice_page()`

## `customer/make_payment.js`

@file customer/make_payment.js; @description Customer payment amount/method selection and invoice create.; @see docs/api/javascript.md

- `function submit_checkout()`
- `function get_selected_payment_method_id()`
- `function get_selected_payment_amount()`
- `function init_customer_payment_page()`

## `customer/parcels.js`

@file customer/parcels.js; @description Reserve selected parcels for an open pickup day.

- `function init_customer_parcels_page()`

## `mgmt/accounts.js`

@file mgmt/accounts.js; @description Management accounts list search.; @see docs/api/javascript.md

- `function search_accounts()`
- `function init_account_mgmt_page()` — Initialize account management page.

## `mgmt/carriers.js`

@file mgmt/carriers.js; @description Carrier management form save/add/remove.; @see docs/api/javascript.md

- `function init_carrier_mgmt_page()`

## `mgmt/charges.js`

@file mgmt/charges.js; @description Charge rules and tax settings form handling.; @see docs/api/javascript.md

- `function init_charges_mgmt_page()`

## `mgmt/email.js`

@file mgmt/email.js; @description Email settings (sender + notification rules) form.; @see docs/api/javascript.md

- `function init_email_mgmt_page()`

## `mgmt/email_template.js`

@file mgmt/email_template.js; @description Jodit email template editor and save/load.; @see docs/api/javascript.md

- `function make_token_btn()` — Build a Jodit toolbar control that inserts a stable token chip. @param {{name: string, text: string, token: string}} spec @returns {object}
- `function mark_email_template_dirty()` — Mark the editor form dirty unless updates are suppressed (load/reset).
- `function clear_email_template_dirty()` — Clear dirty flag after load or successful save.
- `function hide_add_template_modal()` — Hide the add-template modal via Bootstrap 5 API.
- `function ensure_email_template_editor()` — Create the single Jodit instance if not already created. @returns {object|null}
- `function set_editor_value()` — Set editor HTML via editor.value only. @param {string} html
- `function get_editor_value()` — Read editor HTML via editor.value only. @returns {string}
- `function load_email_template()` — Load a template's subject/body into the form. @param {string|number} id
- `function init_email_template_mgmt_page()` — Initialize email template editor page.

## `mgmt/general.js`

@file mgmt/general.js; @description GlobalSettings general business info and logo upload.; @see docs/api/javascript.md

- `function init_general_mgmt_page()`

## `mgmt/pickup.js`

@file mgmt/pickup.js; @description Staff pickup schedule rules and day CRUD.

- `function init_pickup_mgmt_page()`

## `mgmt/types.js`

@file mgmt/types.js; @description Package type management form save/add/remove.; @see docs/api/javascript.md

- `function init_types_mgmt_page()`

## `mgmt/user_detail.js`

@file mgmt/user_detail.js; @description Staff user detail: access, password, account links, invites.

- `function init_user_detail_page()`

## `mgmt/users.js`

@file mgmt/users.js; @description Management users list search/filter.

- `function search_users()`
- `function init_user_mgmt_page()`

## `modals/edit_queue_name.js`

@file modals/edit_queue_name.js; @description Modal to rename a check-in queue.; @see docs/api/javascript.md

- `function edit_queue_name()`

## `modals/email_contents.js`

@file modals/email_contents.js; @description Modal to view sent email HTML contents.; @see docs/api/javascript.md

- `function email_contents()`

## `modals/new_acct.js`

@file modals/new_acct.js; @description Modal workflow to create a user and/or billing account, or send a signup invite.; @see docs/api/javascript.md

- `function new_acct_portal_mode()`
- `function new_acct_sync_fields()`
- `function new_acct()`

## `modals/picklist_mgmt.js`

@file modals/picklist_mgmt.js; @description Picklist create/edit modal and list actions.; @see docs/api/javascript.md

- `function picklist_list_page()` — Picklist management modal interactions.

## `modals/row.js`

@file modals/row.js; @description Per-row package edit modal and bulk row updates.; @see docs/api/javascript.md

- `function setup_actions()` — Bind per-row action buttons on package tables.
- `function init_edit_modal()` — Populate and show the row edit modal.
- `function handle_updated_rows()` — Refresh rows after a successful edit POST.
- `function row_modals()` — Initialize row modal subsystem.

## `profile.js`

@file profile.js; @description My Profile form submit and email list management.; @see docs/api/javascript.md

- `function init_profile_page()`

## `reports/details.js`

@file reports/details.js; @description Report builder UI: field config JSON payload.; @see docs/api/javascript.md

- `function prepare_json_payload()`
- `function toggle_create_button()` — Enable/disable report create based on form validity.
- `function toggle_row_arrows()` — Update field-order arrow button states.
- `function init_report_details_page()` — Initialize report create/edit builder.

## `reports/report_chart.js`

@file reports/report_chart.js; @description Chart.js rendering for dashboard stats.; @see docs/api/javascript.md

- `function carrier_datasets()` — Build Chart.js datasets from packages_by_carrier y_data.
- `function update_carrier_chart()` — Update or create the packages-by-carrier chart.
- `function toggle_disabled_chart_buttons()`
- `function update_chart()` — Fetch and redraw the dashboard chart for a frequency.
- `function init_report_chart()` — Create the initial Chart.js instance.

## `reports/report_list.js`

@file reports/report_list.js; @description Saved reports list actions.; @see docs/api/javascript.md

- `function init_report_list()`

## `reports/view.js`

@file reports/view.js; @description Report view page with PDF generation status polling.; @see docs/api/javascript.md

- `function update_ui()`
- `function init_report_view_page()` — Start PDF status polling on report view.

## `searchbox.js`

@file searchbox.js; @description Package search filters and Select2-backed search box.; @see docs/api/javascript.md

- `function change_selected_filter()`
- `function init_searchbox_page()` — Initialize package search box and Select2.

## `table_select.js`

@file table_select.js; @description Checkbox multi-select with shift-click and pagination links.; @see docs/api/javascript.md

- `function update_pagination_links()`
- `function handle_shift_select()` — Select a range of checkboxes between last and current.
- `function update_package_selection()` — Track selected package ids when a checkbox toggles.
- `function init_checkbox()` — Initialize table checkbox selection behavior.

## `user_edit.js`

@file user_edit.js; @description Staff user/account edit: aliases, emails, create user AJAX.; @see docs/api/javascript.md

- `function init_user_edit_page()`
