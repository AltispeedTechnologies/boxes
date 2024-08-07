function init_charges_mgmt_page() {
    $("input#taxrate").off("input").on("input", function() {
        window.format_price_input($(this));
    });

    $("#add-charge-template").off("click").on("click", function() {
        var new_entry = $(".charge-template.d-none").clone().removeClass("d-none");
        new_entry.find(".remove-charge-template").click(function() {
            $(this).closest(".charge-template").remove();
        });
        $("#charges-templates").append(new_entry);
    });

    $(".remove-charge-template").off("click").on("click", function() {
        $(this).closest(".charge-template").remove();
    });

    $("#add-custom-charge-template").off("click").on("click", function() {
        var new_entry = $(".custom-charge-template.d-none").clone().removeClass("d-none");
        new_entry.find(".remove-custom-charge-template").click(function() {
            $(this).closest(".custom-charge-template").remove();
        });
        $("#custom-charges-templates").append(new_entry);
    });

    $(".remove-custom-charge-template").off("click").on("click", function() {
        $(this).closest(".custom-charge-template").remove();
    });

    // Customer-Facing Charges and UI updates
    $("input#stripefees").off("change").on("change", function() {
        var checked = $(this).prop("checked");
        $("label[for=\"stripefees\"]").first().toggleClass("fw-bold", !checked);
        $("label[for=\"stripefees\"]").last().toggleClass("fw-bold", checked);
    });
    $("input#enabletaxes").off("change").on("change", function() {
        var checked = $(this).prop("checked");
        $("div#taxrateinput").toggleClass("d-none", !checked);
    });

    $("#savebtn").off("click").on("click", function() {
        $("#savingicon").show();

        let charge_rules = [];

        $(".charge-template:not(.d-none)").each(function() {
            var days = $(this).find("#days").val();
            if (days) {
                charge_rules.push({ days: days });
            }
        });

        $(".custom-charge-template:not(.d-none)").each(function() {
            var package_type_id = $(this).find("#package_type").val();
            var days = $(this).find("#days").val();
            var price = $(this).find("#price").val();
            var frequency = $(this).find("#frequency").val();
            if (package_type_id && days && price && frequency) {
                charge_rules.push({
                    package_type_id: package_type_id,
                    days: days,
                    price: price,
                    frequency: frequency
                });
            }
        });

        charge_rules.push({ endpoint: $("#endpoint").val() });

        var misc_charges = {};
        misc_charges["pass_on_fees"] = $("input#stripefees").prop("checked");
        misc_charges["taxes"] = $("input#enabletaxes").prop("checked");
        if (misc_charges["taxes"]) {
            let tax_rate = $("input#taxrate").val();

            // Filter out empty strings and non-number chars
            if (tax_rate === "") {
                window.display_error_message(["No tax rate specified"]);
                return;
            } else if (isNaN(tax_rate)) {
                window.display_error_message(["Invalid value for tax rate"]);
                return;
            }

            // 0 < x < 100
            tax_rate = parseFloat(tax_rate);
            if (tax_rate <= 0 || tax_rate >= 100) {
                window.display_error_message(["Invalid value for tax rate"]);
                return;
            }

            misc_charges["tax_rate"] = tax_rate;
        }

        var payload = {
            charge_rules: charge_rules,
            misc_charges: misc_charges
        };

        window.ajax_request({
            type: "POST",
            url: "/mgmt/charges/update",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function() {
                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
            }
        });
    });
}

window.manage_init_func("div#chargesmgmt", "charges", init_charges_mgmt_page);
