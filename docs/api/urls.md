# HTTP routes (generated)

Resolved from the live URLConf. Access tier uses decorator `access_tier` metadata when present, otherwise pattern-list membership in `boxes.urls`.

| Tier | Path | Name | Callable | Summary |
|------|------|------|----------|---------|
| public | `login/` | `login` | `boxes.views.auth.sign_in` | Render login form or authenticate and redirect (honors ``next``). |
| public | `signup/<str:token>/` | `signup` | `boxes.views.auth.signup` | Public self-registration **only** via a valid staff-issued invite token. |
| public | `webhooks/mailjet` | `mailjet_webhooks` | `boxes.views.webhooks.mailjet_webhooks` | POST: accept Mailjet Event API payloads and store SentEmailEvent rows. |
| public | `webhooks/stripe` | `stripe_webhooks` | `boxes.views.webhooks.stripe_webhooks` | POST: verify Stripe signature and enqueue payment handling. |
| authenticated | `` | `home` | `boxes.views.index.index` | Render customer home, or send warehouse roles to packages/check-in. |
| authenticated | `logout/` | `logout` | `boxes.views.auth.sign_out` | Log out the current user and redirect to the login page (full document). |
| authenticated | `profile/` | `profile_user` | `boxes.views.user.profile_user` | Self-service profile for the logged-in CustomUser. |
| authenticated | `profile/emails/update` | `update_profile_emails` | `boxes.views.user.update_profile_emails` | Create/update/remove CustomUserEmail rows for the authenticated user only. |
| authenticated | `profile/update` | `update_profile` | `boxes.views.user.update_profile` | Update the authenticated user's profile fields (and optional password). |
| delivery | `accounts/<int:pk>/packages` | `account_packages` | `boxes.views.account.account_packages` | List packages belonging to an account. |
| delivery | `accounts/search` | `account_search` | `boxes.views.account.account_search` | JSON/Select2 search over accounts and aliases. |
| delivery | `carriers/search` | `carrier_search` | `boxes.views.carrier.carrier_search` | GET: search carriers by name. |
| delivery | `packages/` | `packages` | `boxes.views.packages.search.all_packages` | GET: all-packages listing. |
| delivery | `packages/<int:pk>` | `package_detail` | `boxes.views.packages.package.package_detail` | GET: package detail page with history. |
| delivery | `packages/<int:pk>/update` | `update_package` | `boxes.views.packages.package.update_package` | POST: update fields on one package. |
| delivery | `packages/checkin` | `check_in` | `boxes.views.packages.check_in.check_in` | GET: check-in page with queue selector. |
| delivery | `packages/checkin/create` | `create_package` | `boxes.views.packages.check_in.create_package` | POST: create a package (and queue membership) from form or JSON body. |
| delivery | `packages/checkin/submit` | `check_in_packages` | `boxes.views.packages.check_in.check_in_packages` | POST: transition selected packages to checked-in state. |
| delivery | `packages/label` | `show_label` | `boxes.views.labels.show_label` | GET: label print UI. |
| delivery | `packages/label/pdf` | `generate_label` | `boxes.views.labels.generate_label` | GET: stream multi-label PDF for requested packages. |
| delivery | `packages/search` | `search_packages` | `boxes.views.packages.search.search_packages` | GET: search packages by query/filters. |
| delivery | `packages/update` | `update_packages` | `boxes.views.packages.package.update_packages` | POST: bulk update package fields. |
| delivery | `picklists/` | `picklists` | `boxes.views.picklists.picklist_list` | GET: picklist index page. |
| delivery | `picklists/<int:pk>/packages` | `picklist_show` | `boxes.views.picklists.picklist_show` | GET: picklist detail page. |
| delivery | `picklists/<int:pk>/packages/table` | `picklist_show_table` | `boxes.views.picklists.picklist_show_table` | GET: packages table fragment for a picklist. |
| delivery | `picklists/modify` | `modify_package_picklist` | `boxes.views.picklists.modify_package_picklist` | POST: assign packages to a picklist. |
| delivery | `picklists/query` | `picklist_query` | `boxes.views.picklists.picklist_query` | GET: query picklists for UI widgets. |
| delivery | `queues/<int:pk>/packages` | `queue_packages` | `boxes.views.packages.backend.queue_packages` | GET: packages currently in queue ``pk``. |
| delivery | `types/search` | `type_search` | `boxes.views.packages.backend.type_search` | GET: PackageType Select2 search. |
| staff | `accounts/<int:pk>/edit` | `account_edit` | `boxes.views.account.account_edit` | Render staff account edit page. |
| staff | `accounts/<int:pk>/emails` | `account_emails` | `boxes.views.account.account_emails` | List sent emails related to an account. |
| staff | `accounts/<int:pk>/ledger` | `account_ledger` | `boxes.views.account.account_ledger` | Render or return ledger rows for an account. |
| staff | `accounts/<int:pk>/members/create` | `account_members_create_web` | `boxes.views.account.account_members_create_web` | POST (staff): create a new web portal login and link it to this account. |
| staff | `accounts/<int:pk>/members/disassociate` | `account_members_disassociate` | `boxes.views.account.account_members_disassociate` | POST (staff): soft-disassociate a user from this account by user_id. |
| staff | `accounts/<int:pk>/members/link` | `account_members_link` | `boxes.views.account.account_members_link` | POST (staff): link a user to this account by user_id or username. |
| staff | `accounts/<int:pk>/update` | `update_account` | `boxes.views.account.update_account` | POST: update account fields (name, billable, comments, etc.). |
| staff | `accounts/<int:pk>/waiver` | `account_fee_waiver` | `boxes.views.account.account_fee_waiver` | POST: staff credit waiver on account ledger (account_id from URL). |
| staff | `accounts/aliases/update` | `update_account_aliases` | `boxes.views.account.update_account_aliases` | POST: replace/update account alias list. |
| staff | `emails/<int:pk>/contents` | `get_email_contents` | `boxes.views.emails.get_email_contents` | GET: return HTML body for a SentEmail primary key. |
| staff | `mgmt/accounts` | `account_mgmt` | `boxes.views.mgmt.accounts.account_mgmt` | GET: management accounts list/search UI. |
| staff | `mgmt/charges` | `charge_settings` | `boxes.views.mgmt.charges.charge_settings` | GET: charges and tax configuration page. |
| staff | `mgmt/charges/update` | `save_charge_settings` | `boxes.views.mgmt.charges.save_charge_settings` | POST: persist AccountChargeSettings and tax GlobalSettings fields. |
| staff | `mgmt/email/configure` | `email_settings` | `boxes.views.mgmt.email.email_settings` | GET: sender and notification rules page. |
| staff | `mgmt/email/logs` | `email_logs` | `boxes.views.mgmt.email.email_logs` | GET: sent email log listing. |
| staff | `mgmt/email/templates` | `email_template` | `boxes.views.mgmt.email_templates.email_template` | GET: template list/editor page. |
| staff | `mgmt/email/templates/add` | `add_email_template` | `boxes.views.mgmt.email_templates.add_email_template` | POST: create a new EmailTemplate. |
| staff | `mgmt/email/templates/fetch` | `email_template_content` | `boxes.views.mgmt.email_templates.email_template_content` | GET: fetch subject/body for a template id. |
| staff | `mgmt/email/templates/update` | `update_email_template` | `boxes.views.mgmt.email_templates.update_email_template` | POST: update template name/subject/content. |
| staff | `mgmt/email/update` | `save_email_settings` | `boxes.views.mgmt.email.save_email_settings` | POST: save EmailSettings and NotificationRule rows. |
| staff | `mgmt/general` | `general_settings` | `boxes.views.mgmt.general.general_settings` | GET: general settings page. |
| staff | `mgmt/general/update` | `save_general_settings` | `boxes.views.mgmt.general.save_general_settings` | POST: save GlobalSettings fields and process logo upload. |
| staff | `mgmt/packages/carriers` | `carrier_settings` | `boxes.views.mgmt.carriers.carrier_settings` | GET: carriers management page. |
| staff | `mgmt/packages/carriers/update` | `update_carriers` | `boxes.views.mgmt.carriers.update_carriers` | POST: create/update/delete carriers from form data. |
| staff | `mgmt/packages/types` | `package_type_settings` | `boxes.views.mgmt.types.package_type_settings` | GET: package types management page. |
| staff | `mgmt/packages/types/update` | `update_package_types` | `boxes.views.mgmt.types.update_package_types` | POST: create/update/delete package types. |
| staff | `mgmt/pickup` | `pickup_mgmt` | `boxes.views.mgmt.pickup.pickup_mgmt` | GET: staff pickup days and schedule rules management page. |
| staff | `mgmt/pickup/days/update` | `update_pickup_days` | `boxes.views.mgmt.pickup.update_pickup_days` | POST: create/update pickup days (date, is_active, notes, picklist). |
| staff | `mgmt/pickup/open` | `pickup_open_days` | `boxes.views.mgmt.pickup.pickup_open_days` | GET: JSON open pickup dates in a window (start/end query params). |
| staff | `mgmt/pickup/rules/update` | `update_pickup_rules` | `boxes.views.mgmt.pickup.update_pickup_rules` | POST: create/update/delete schedule rules from JSON payload. |
| staff | `mgmt/users` | `user_mgmt` | `boxes.views.user.user_mgmt` | GET (staff): list/search portal and staff users independently of accounts. |
| staff | `modals/actions` | `get_actions_modals` | `boxes.views.modals.get_actions_modals` | Return row-action modal markup. |
| staff | `modals/bulk` | `get_bulk_modals` | `boxes.views.modals.get_bulk_modals` | Return bulk-action modal markup. |
| staff | `modals/picklistmgmt` | `get_picklist_mgmt_modals` | `boxes.views.modals.get_picklist_mgmt_modals` | Return picklist management modal markup. |
| staff | `packages/checkout` | `check_out` | `boxes.views.packages.check_out.check_out` | GET: check-out page. |
| staff | `packages/checkout/reverse` | `check_out_packages_reverse` | `boxes.views.packages.check_out.check_out_packages_reverse` | POST: reverse a check-out back to checked-in. |
| staff | `packages/checkout/submit` | `check_out_packages` | `boxes.views.packages.check_out.check_out_packages` | POST: check out packages (state → Checked out). |
| staff | `packages/checkout/verify` | `verify_can_checkout` | `boxes.views.packages.check_out.verify_can_checkout` | POST: validate packages can be checked out (paid/balance rules). |
| staff | `picklists/<int:pk>/checkout` | `picklist_check_out` | `boxes.views.picklists.picklist_check_out` | GET: checkout flow scoped to a picklist. |
| staff | `picklists/<int:pk>/remove` | `remove_picklist` | `boxes.views.picklists.remove_picklist` | POST: delete a picklist by id. |
| staff | `picklists/create` | `create_picklist` | `boxes.views.picklists.create_picklist` | POST: create a picklist (date/description). |
| staff | `picklists/remove` | `remove_package_picklist` | `boxes.views.picklists.remove_package_picklist` | POST: remove packages from picklists. |
| staff | `queues/<int:pk>/update` | `update_queue_name` | `boxes.views.packages.backend.update_queue_name` | POST: rename a queue. |
| staff | `reports/<int:pk>/csv` | `report_generate_csv` | `boxes.views.reports.frontend.report_view_csv` | GET: stream report as CSV. |
| staff | `reports/<int:pk>/edit` | `report_details` | `boxes.views.reports.frontend.report_details` | GET: create/edit report builder UI. |
| staff | `reports/<int:pk>/pdf` | `report_generate_pdf` | `boxes.views.reports.backend.report_generate_pdf` | Queue or trigger PDF generation for report ``pk``. |
| staff | `reports/<int:pk>/pdf/view` | `report_view_pdf` | `boxes.views.reports.frontend.report_view_pdf` | GET: serve generated PDF if available. |
| staff | `reports/<int:pk>/remove` | `report_remove` | `boxes.views.reports.backend.report_remove` | POST: delete report ``pk``. |
| staff | `reports/<int:pk>/update` | `report_update` | `boxes.views.reports.backend.report_update` | POST: update report ``pk`` config. |
| staff | `reports/<int:pk>/view` | `report_view` | `boxes.views.reports.frontend.report_view` | GET: view report results and generation status. |
| staff | `reports/data` | `report_data` | `boxes.views.reports.frontend.report_data` | GET: dashboard data page shell. |
| staff | `reports/data/view` | `report_data_view` | `boxes.views.reports.frontend.report_data_view` | GET: data/chart fragment for frequency tabs. |
| staff | `reports/list` | `report_list` | `boxes.views.reports.frontend.report_list` | GET: list saved reports. |
| staff | `reports/name` | `report_name_search` | `boxes.views.reports.backend.report_name_search` | POST: check report name availability/search. |
| staff | `reports/new` | `report_new` | `boxes.views.reports.frontend.report_details` | GET: create/edit report builder UI. |
| staff | `reports/new/submit` | `report_new_submit` | `boxes.views.reports.backend.report_new_submit` | POST: create a new Report from config JSON. |
| staff | `reports/stats/chart` | `report_stats_chart` | `boxes.views.reports.backend.report_stats_chart` | POST: return chart data payload for dashboard. |
| staff | `reports/stripe-totals` | `stripe_totals` | `boxes.views.reports.stripe_totals.stripe_totals` | GET: aggregate succeeded invoice money fields for staff reports. |
| staff | `users/<int:pk>/accounts/link` | `user_link_account` | `boxes.views.user.user_link_account` | POST (staff): link this user to a billing account by account_id. |
| staff | `users/<int:pk>/accounts/unlink` | `user_unlink_account` | `boxes.views.user.user_unlink_account` | POST (staff): soft-disassociate this user from a billing account. |
| staff | `users/<int:pk>/edit` | `user_detail` | `boxes.views.user.user_detail` | GET (staff): user detail / edit page (login identity, not billing account). |
| staff | `users/<int:pk>/invite` | `send_user_invite_for` | `boxes.views.user.send_user_invite` | POST (staff): create/send a signup invite (optionally for an existing email). |
| staff | `users/<int:pk>/status` | `update_user_status` | `boxes.views.user.update_user_status` | POST (staff): activate/deactivate user and optional password / groups. |
| staff | `users/emails/update` | `update_user_emails` | `boxes.views.user.update_user_emails` | POST (staff): update notification emails for a target user. |
| staff | `users/invite` | `send_user_invite` | `boxes.views.user.send_user_invite` | POST (staff): create/send a signup invite (optionally for an existing email). |
| staff | `users/new` | `create_user` | `boxes.views.user.create_user` | POST (staff): create user and/or billing account, or send a signup invite. |
| staff | `users/search` | `user_search` | `boxes.views.account.user_search` | JSON/Select2 search over users for membership linking. |
| staff | `users/update` | `update_user` | `boxes.views.user.update_user` | POST (staff): update a target user's profile fields. |
| customer | `customer/invoices` | `customer_invoices` | `boxes.views.customer.customer_invoices` | GET: past invoices for the active account. |
| customer | `customer/ledger` | `customer_ledger` | `boxes.views.customer.customer_ledger` | GET: ledger history for the active account. |
| customer | `customer/parcels` | `customer_parcels` | `boxes.views.customer.customer_parcels` | GET: customer package list for linked account. |
| customer | `customer/parcels/reserve` | `customer_reserve_pickup` | `boxes.views.customer_pickup.customer_reserve_pickup` | POST: reserve selected packages for an open pickup day. |
| customer | `customer/payments` | `customer_make_payment` | `boxes.views.customer.customer_make_payment` | GET: payment page with balance and methods. |
| customer | `customer/payments/portal` | `customer_payment_methods` | `boxes.views.customer.customer_payment_methods` | GET: payment methods data for UI. |
| customer | `customer/payments/portal/redir` | `customer_billing_portal` | `boxes.views.customer.customer_billing_portal` | GET: redirect to Stripe Billing Portal session. |
| customer | `customer/pickup/open` | `customer_open_pickup_days` | `boxes.views.customer_pickup.customer_open_pickup_days` | GET: JSON open pickup dates for the customer reservation UI. |
| customer | `customer/select-account` | `customer_select_account` | `boxes.views.customer.customer_select_account` | GET: list linked accounts. POST: set active account in session. |
| customer | `invoice/<int:pk>` | `customer_view_invoice` | `boxes.views.customer.customer_view_invoice` | GET: invoice detail / confirmation page. |
| customer | `invoice/<int:pk>/cancel` | `customer_cancel_invoice` | `boxes.views.customer.customer_cancel_invoice` | GET: cancel an open invoice/PaymentIntent. |
| customer | `invoice/<int:pk>/confirm` | `customer_confirm_invoice` | `boxes.views.customer.customer_confirm_invoice` | POST: confirm and finalize payment for invoice. |
| customer | `invoice/<int:pk>/pdf` | `customer_view_pdf` | `boxes.views.customer.customer_view_pdf` | GET: invoice PDF download/view. |
| customer | `invoice/new` | `customer_new_invoice` | `boxes.views.customer.customer_new_invoice` | POST: create invoice/PaymentIntent for amount and method. |
| customer | `session/account` | `session_set_active_account` | `boxes.views.customer.session_set_active_account` | POST: set session active account after membership check. |

_Generated 112 application routes (Django admin omitted)._
