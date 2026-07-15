/**
 * @file customer/billing_portal.js
 * @description Stripe Billing Portal redirect helpers.
 * @see docs/api/javascript.md
 */

window.ajax_request({
    type: "GET",
    url: "/customer/payments/portal/redir",
    on_success: function(response) {
        window.location.href = response.url;
    }
});
