function init_customer_payment_page() {
    $("input#otheramountinput").off("input").on("input", function() {
        window.format_price_input($(this));
    });

    // Selecting another payment method
    $("#paymentmethodsdropdown a").off("click").on("click", function() {
        $("#currentpaymentmethod").html($(this).html());

        $("#paymentmethodsdropdown a").removeClass("active");
        $(this).addClass("active");
    });

    $("input[name=\"paymentamount\"]").off("change").on("change", function() {
        let hide_input_box = $(this).attr("id") !== "otheramount";
        $("div#enterotherinput").toggleClass("d-none", hide_input_box);
    });
}

window.manage_init_func("div#customercharges", "make_payment", init_customer_payment_page);
