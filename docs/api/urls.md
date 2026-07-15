# HTTP routes (generated)

Resolved from the live URLConf. Access tier uses decorator `access_tier` metadata when present, otherwise pattern-list membership in `boxes.urls`.

| Tier | Path | Name | Callable | Summary |
|------|------|------|----------|---------|
| public | `login/` | `login` | `boxes.views.auth.sign_in` | Render login form or authenticate and redirect (honors ``next``). |
| public | `webhooks/stripe` | `stripe_webhooks` | `boxes.views.webhooks.stripe_webhooks` | POST: verify Stripe signature and enqueue payment handling. |
| authenticated | `profile/` | `profile_user` | `boxes.views.user.profile_user` | Self-service profile for the logged-in CustomUser. |
| authenticated | `profile/emails/update` | `update_profile_emails` | `boxes.views.user.update_profile_emails` | Create/update/remove CustomUserEmail rows for the authenticated user only. |
| authenticated | `profile/update` | `update_profile` | `boxes.views.user.update_profile` | Update the authenticated user's profile fields (and optional password). |
| staff | `accounts/<int:pk>/edit` | `account_edit` | `boxes.views.account.account_edit` | Render staff account edit page. |
| staff | `accounts/<int:pk>/emails` | `account_emails` | `boxes.views.account.account_emails` | List sent emails related to an account. |
| staff | `accounts/<int:pk>/ledger` | `account_ledger` | `boxes.views.account.account_ledger` | Render or return ledger rows for an account. |
| staff | `accounts/<int:pk>/packages` | `account_packages` | `boxes.views.account.account_packages` | List packages belonging to an account. |
| staff | `accounts/<int:pk>/update` | `update_account` | `boxes.views.account.update_account` | POST: update account fields (name, billable, comments, etc.). |
| staff | `accounts/aliases/update` | `update_account_aliases` | `boxes.views.account.update_account_aliases` | POST: replace/update account alias list. |
| staff | `accounts/search` | `account_search` | `boxes.views.account.account_search` | JSON/Select2 search over accounts and aliases. |
| staff | `carriers/search` | `carrier_search` | `boxes.views.carrier.carrier_search` | GET: search carriers by name. |
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
| staff | `modals/actions` | `get_actions_modals` | `boxes.views.modals.get_actions_modals` | Return row-action modal markup. |
| staff | `modals/bulk` | `get_bulk_modals` | `boxes.views.modals.get_bulk_modals` | Return bulk-action modal markup. |
| staff | `modals/picklistmgmt` | `get_picklist_mgmt_modals` | `boxes.views.modals.get_picklist_mgmt_modals` | Return picklist management modal markup. |
| staff | `packages/` | `packages` | `boxes.views.packages.search.all_packages` | GET: all-packages listing. |
| staff | `packages/<int:pk>` | `package_detail` | `boxes.views.packages.package.package_detail` | GET: package detail page with history. |
| staff | `packages/<int:pk>/update` | `update_package` | `boxes.views.packages.package.update_package` | POST: update fields on one package. |
| staff | `packages/checkin` | `check_in` | `boxes.views.packages.check_in.check_in` | GET: check-in page with queue selector. |
| staff | `packages/checkin/create` | `create_package` | `boxes.views.packages.check_in.create_package` | POST: create a package (and queue membership) from form data. |
| staff | `packages/checkin/submit` | `check_in_packages` | `boxes.views.packages.check_in.check_in_packages` | POST: transition selected packages to checked-in state. |
| staff | `packages/checkout` | `check_out` | `boxes.views.packages.check_out.check_out` | GET: check-out page. |
| staff | `packages/checkout/reverse` | `check_out_packages_reverse` | `boxes.views.packages.check_out.check_out_packages_reverse` | POST: reverse a check-out back to checked-in. |
| staff | `packages/checkout/submit` | `check_out_packages` | `boxes.views.packages.check_out.check_out_packages` | POST: check out packages (state → Checked out). |
| staff | `packages/checkout/verify` | `verify_can_checkout` | `boxes.views.packages.check_out.verify_can_checkout` | POST: validate packages can be checked out (paid/balance rules). |
| staff | `packages/label` | `show_label` | `boxes.views.labels.show_label` | GET: label print UI. |
| staff | `packages/label/pdf` | `generate_label` | `boxes.views.labels.generate_label` | GET: stream multi-label PDF for requested packages. |
| staff | `packages/search` | `search_packages` | `boxes.views.packages.search.search_packages` | GET: search packages by query/filters. |
| staff | `packages/update` | `update_packages` | `boxes.views.packages.package.update_packages` | POST: bulk update package fields. |
| staff | `picklists/` | `picklists` | `boxes.views.picklists.picklist_list` | GET: picklist index page. |
| staff | `picklists/<int:pk>/checkout` | `picklist_check_out` | `boxes.views.picklists.picklist_check_out` | GET: checkout flow scoped to a picklist. |
| staff | `picklists/<int:pk>/packages` | `picklist_show` | `boxes.views.picklists.picklist_show` | GET: picklist detail page. |
| staff | `picklists/<int:pk>/packages/table` | `picklist_show_table` | `boxes.views.picklists.picklist_show_table` | GET: packages table fragment for a picklist. |
| staff | `picklists/<int:pk>/remove` | `remove_picklist` | `boxes.views.picklists.remove_picklist` | POST: delete a picklist by id. |
| staff | `picklists/create` | `create_picklist` | `boxes.views.picklists.create_picklist` | POST: create a picklist (date/description). |
| staff | `picklists/modify` | `modify_package_picklist` | `boxes.views.picklists.modify_package_picklist` | POST: assign packages to a picklist. |
| staff | `picklists/query` | `picklist_query` | `boxes.views.picklists.picklist_query` | GET: query picklists for UI widgets. |
| staff | `picklists/remove` | `remove_package_picklist` | `boxes.views.picklists.remove_package_picklist` | POST: remove packages from picklists. |
| staff | `queues/<int:pk>/packages` | `queue_packages` | `boxes.views.packages.backend.queue_packages` | GET: packages currently in queue ``pk``. |
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
| staff | `types/search` | `type_search` | `boxes.views.packages.backend.type_search` | GET: PackageType Select2 search. |
| staff | `users/emails/update` | `update_user_emails` | `boxes.views.user.update_user_emails` | POST (staff): update notification emails for a target user. |
| staff | `users/new` | `create_user` | `boxes.views.user.create_user` | POST (staff): create user, optional account link, set groups. |
| staff | `users/update` | `update_user` | `boxes.views.user.update_user` | POST (staff): update a target user's profile fields. |
| customer | `` | `home` | `boxes.views.index.index` | Render customer home, or send staff-only users to packages. |
| customer | `customer/parcels` | `customer_parcels` | `boxes.views.customer.customer_parcels` | GET: customer's package list for linked account. |
| customer | `customer/payments` | `customer_make_payment` | `boxes.views.customer.customer_make_payment` | GET: payment page with balance and methods. |
| customer | `customer/payments/portal` | `customer_payment_methods` | `boxes.views.customer.customer_payment_methods` | GET: payment methods data for UI. |
| customer | `customer/payments/portal/redir` | `customer_billing_portal` | `boxes.views.customer.customer_billing_portal` | GET: redirect to Stripe Billing Portal session. |
| customer | `invoice/<int:pk>` | `customer_view_invoice` | `boxes.views.customer.customer_view_invoice` | GET: invoice detail / confirmation page. |
| customer | `invoice/<int:pk>/cancel` | `customer_cancel_invoice` | `boxes.views.customer.customer_cancel_invoice` | GET: cancel an open invoice/PaymentIntent. |
| customer | `invoice/<int:pk>/confirm` | `customer_confirm_invoice` | `boxes.views.customer.customer_confirm_invoice` | POST: confirm and finalize payment for invoice. |
| customer | `invoice/<int:pk>/pdf` | `customer_view_pdf` | `boxes.views.customer.customer_view_pdf` | GET: invoice PDF download/view. |
| customer | `invoice/new` | `customer_new_invoice` | `boxes.views.customer.customer_new_invoice` | POST: create invoice/PaymentIntent for amount and method. |
| customer | `logout/` | `logout` | `boxes.views.auth.sign_out` | Log out the current user and redirect to login. |

_Generated 87 application routes (Django admin omitted)._
