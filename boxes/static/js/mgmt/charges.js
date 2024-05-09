$(document).ready(function() {
    $("#add-charge-template").click(function() {
        var new_entry = $(".charge-template.d-none").clone().removeClass("d-none");
        new_entry.find(".remove-charge-template").click(function() {
            $(this).closest(".charge-template").remove();
        });
        $("#charges-templates").append(new_entry);
    });

    $(".remove-charge-template").click(function() {
        $(this).closest(".charge-template").remove();
    });

    $("#add-custom-charge-template").click(function() {
        var new_entry = $(".custom-charge-template.d-none").clone().removeClass("d-none");
        new_entry.find(".remove-custom-charge-template").click(function() {
            $(this).closest(".custom-charge-template").remove();
        });
        $("#custom-charges-templates").append(new_entry);
    });

    $(".remove-custom-charge-template").click(function() {
        $(this).closest(".custom-charge-template").remove();
    });

    $("#savebtn").click(function() {
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

        $.ajax({
            url: "/mgmt/charges/update",
            type: "POST",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            data: JSON.stringify(charge_rules),
            success: function(response) {
                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
            }
        });
    });
});
