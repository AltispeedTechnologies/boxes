/**
 * @file customer/confirm_payment.js
 * @description Invoice confirmation and client-side payment completion.
 * @see docs/api/javascript.md
 */

function init_invoice_page() {
    $("button#confirmbtn, a#retrypayment").off("click").on("click", function() {
        let invoice_id = $(this).data("id");

        let processing_html = "<h4 class=\"text-warning\"><i class=\"fa-solid fa-spinner fa-spin\"></i> ";
        processing_html += "Processing</h4>";
        $("div#invoicepaymentstatus").html(processing_html);

        window.ajax_request({
            type: "POST",
            url: "/invoice/" + invoice_id + "/confirm",
            on_success: function(response) {
                if (response.url) {
                    window.location.href = response.url;
                } else {
                    window.location.href = "/invoice/" + invoice_id;
                }
            }
        });
    });
}

$(init_invoice_page);
