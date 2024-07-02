function init_payment_methods_page() {
    $("#addpaymentmethod").off("click").on("click", function() {
        $(this).css("cursor", "progress");
        window.ajax_request({
            type: "GET",
            url: "/customer/payments/methods/create",
            on_success: function(response) {
                window.location.href = response.url;
            }
        });
    });
}

window.manage_init_func("div#customerpaymentmethods", "payment_methods", init_payment_methods_page);
