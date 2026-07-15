/**
 * @file customer/make_payment.js
 * @description Customer payment amount/method selection and invoice create.
 * @see docs/api/javascript.md
 */

function submit_checkout(payment_amount, payment_method_id) {
    $("#checkoutloading").removeClass("d-none");
    $("button#checkoutbtn").attr("disabled", true);

    var payload = { amount: payment_amount, method: payment_method_id };

    window.ajax_request({
        type: "POST",
        url: "/invoice/new",
        payload: JSON.stringify(payload),
        content_type: "application/json",
        on_success: function(response) {
            window.location.href = response.url;
        },
        on_response: function(response) {
            if (!response.success) {
                $("#checkoutloading").addClass("d-none");
                $("button#checkoutbtn").attr("disabled", false);
            }
        }
    });
}

function get_selected_payment_method_id() {
    if ($("input[name=\"paymentmethod\"]:checked").attr("id") === "onetimemethod") {
        return "ONETIME";
    }
    return $("button#currentpaymentmethod").attr("data-id");
}

function get_selected_payment_amount(current_balance) {
    var payment_amount_selection = $("input[name=\"paymentamount\"]:checked").attr("id");
    if (payment_amount_selection === "otheramount") {
        return parseFloat($("input#otheramountinput").val());
    }
    return current_balance;
}

function init_customer_payment_page() {
    $("input#otheramountinput").off("input").on("input", function() {
        window.format_price_input($(this));
    });

    $("input[name=\"paymentamount\"]").off("change").on("change", function() {
        var hide_input_box = $(this).attr("id") !== "otheramount";
        $("div#enterotherinput").toggleClass("d-none", hide_input_box);
    });

    $("input[name=\"paymentmethod\"]").off("change").on("change", function() {
        var hide_dropdown = $(this).attr("id") !== "selectmethod";
        $("#currentpaymentmethod").toggleClass("d-none", hide_dropdown);
    });

    $("#paymentmethodsdropdown a").off("click").on("click", function() {
        $("#currentpaymentmethod").html($(this).html());
        $("#currentpaymentmethod").attr("data-id", $(this).attr("data-id"));

        $("#paymentmethodsdropdown a").removeClass("active");
        $(this).addClass("active");
    });

    $("button#checkoutbtn").off("click").on("click", function() {
        var current_balance = parseFloat($("input#currentdue").data("balance"));
        if (isNaN(current_balance)) {
            current_balance = 0;
        }

        var payment_method_id = get_selected_payment_method_id();
        var payment_amount = get_selected_payment_amount(current_balance);

        if (isNaN(payment_amount) || payment_amount < 0.5) {
            window.display_error_message(["Enter a valid amount of at least $0.50."]);
            return;
        }

        var payment_amount_selection = $("input[name=\"paymentamount\"]:checked").attr("id");
        if (payment_amount_selection === "otheramount" && current_balance > 0) {
            if (payment_amount > current_balance) {
                $("#over-specified").text(payment_amount.toFixed(2));
                $("#over-due").text(current_balance.toFixed(2));
                $("#over-credit").text((payment_amount - current_balance).toFixed(2));
                var overModal = bootstrap.Modal.getOrCreateInstance(document.getElementById("overPaymentAmountModal"));
                $("#overPaymentConfirm").off("click").on("click", function() {
                    overModal.hide();
                    submit_checkout(payment_amount, payment_method_id);
                });
                overModal.show();
                return;
            }
            if (payment_amount < current_balance) {
                $("#under-specified").text(payment_amount.toFixed(2));
                $("#under-due").text(current_balance.toFixed(2));
                var underModal = bootstrap.Modal.getOrCreateInstance(document.getElementById("underPaymentAmountModal"));
                $("#underPaymentConfirm").off("click").on("click", function() {
                    underModal.hide();
                    submit_checkout(payment_amount, payment_method_id);
                });
                underModal.show();
                return;
            }
        }

        submit_checkout(payment_amount, payment_method_id);
    });
}

$(init_customer_payment_page);
