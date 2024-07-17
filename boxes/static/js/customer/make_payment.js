function init_customer_payment_page() {
    $("input#otheramountinput").off("input").on("input", function() {
        window.format_price_input($(this));
    });

    $("input[name=\"paymentamount\"]").off("change").on("change", function() {
        let hide_input_box = $(this).attr("id") !== "otheramount";
        $("div#enterotherinput").toggleClass("d-none", hide_input_box);
    });

    $("input[name=\"paymentmethod\"]").off("change").on("change", function() {
        let hide_dropdown = $(this).attr("id") !== "selectmethod";
        $("#currentpaymentmethod").toggleClass("d-none", hide_dropdown);
    });

    // Selecting another payment method
    $("#paymentmethodsdropdown a").off("click").on("click", function() {
        $("#currentpaymentmethod").html($(this).html());
        $("#currentpaymentmethod").attr("data-id", $(this).attr("data-id"));

        $("#paymentmethodsdropdown a").removeClass("active");
        $(this).addClass("active");
    });

    $("button#checkoutbtn").off("click").on("click", function() {
        $("#checkoutloading").removeClass("d-none");
        $(this).attr("disabled", true);

        let current_balance = parseFloat($("input#currentdue").data("balance"));

        let payment_method_id;
        if ($("input[name=\"paymentmethod\"]:checked").attr("id") === "onetimemethod") {
            payment_method_id = "ONETIME";
        } else {
            payment_method_id = $("button#currentpaymentmethod").attr("data-id");
        }

        let payment_amount_selection = $("input[name=\"paymentamount\"]:checked").attr("id");
        let payment_amount;

        if (payment_amount_selection === "otheramount") {
            payment_amount = parseFloat($("input#otheramountinput").val());
            if (payment_amount > current_balance) {
                console.log("more than current balance");
            }
        } else {
            payment_amount = current_balance;
        }

        var payload = { amount: payment_amount, method: payment_method_id };

        window.ajax_request({
            type: "POST",
            url: "/invoice/new",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function(response) {
                window.location.href = response.url;
            }
        });
    });
}

window.manage_init_func("div#customercharges", "make_payment", init_customer_payment_page);
