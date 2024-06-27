function init_charges_mgmt_page() {
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
                charge_rules.push({ package_type_id: package_type_id,
                    days: days,
                    price: price,
                    frequency: frequency });
            }
        });

        charge_rules.push({ endpoint: $("#endpoint").val() });

        window.ajax_request({
            type: "POST",
            url: "/mgmt/charges/update",
            payload: JSON.stringify(charge_rules),
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
