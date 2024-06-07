function init_types_mgmt_page() {
    let new_type_id = 0;

    $("#addpkgtype").off("click").on("click", function() {
        let new_row = $(".visually-hidden")
            .clone()
            .removeClass("visually-hidden")
            .attr("data-id", "NEW_" + ++new_type_id);

        $(".visually-hidden").before(new_row);
        $(this).trigger("verifySave");
    });

    $("#savepkgtypes").off("click").on("click", function() {
        $("#savingicon").show();
        var $table = $(document).find("#packagetypes");

        let payload = {};

        $table.find("tr:not(.visually-hidden)").each(function() {
            let data_id = $(this).attr("data-id");
            let shortcode = $(this).find("td[data-type=\"shortcode\"] span.text").text().trim();
            let description = $(this).find("td[data-type=\"description\"] span.text").text().trim();
            let default_price = $(this).find("td[data-type=\"default_price\"] span.text").text().trim();
            payload[data_id] = {shortcode: shortcode, description: description, default_price: default_price};
        });

        $.ajax({
            url: "/mgmt/packages/types/update",
            type: "POST",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            data: JSON.stringify(payload),
            success: function(response) {
                if (response.success) {
                    $.each(response.updated_types, function(key, new_id) {
                        $table.find("tr[data-id=\"" + key + "\"]").attr("data-id", new_id);
                    });

                    $("#savingicon").hide();
                    $("#successicon").show();
                    $("#successicon").fadeOut(2000);
                }
            },
            error: function() {
                alert("Error saving settings.");
            }
        });
    });

    $("#packagetypes").off("input", "input.form-control").on("input", "input.form-control", function() {
        var row = $(this).closest("tr");
        var confirm_button = row.find(".confirmrow");

        row.find("input.form-control").each(function() {
            if ($(this).hasClass("default_price")) {
                window.format_price_input($(this));
            } else {
                $(this).toggleClass("is-invalid", $(this).val().trim() === "");
            }
        });

        var is_shortcode_filled = row.find("input.shortcode").val().trim() !== "";
        var is_description_filled = row.find("input.description").val().trim() !== "";
        var is_price_filled = row.find("input.default_price").val().trim() !== "";
        var disabled = !(is_shortcode_filled && is_description_filled && is_price_filled);

        confirm_button.prop("disabled", disabled);
    });

    $(document).off("click", ".editrow, .confirmrow").on("click", ".editrow, .confirmrow", function() {
        var $parent_tr = $(this).closest("tr");
        var editing = $(this).hasClass("editrow");

        $parent_tr.find("td").each(function() {
            var $text = $(this).find(".text");
            var $input = $(this).find(".form-control");
            if ($text.length === 0 || $input.length === 0) { return true; }

            if (editing) {
                $input.val($text.text().trim());
            } else {
                $text.text($input.val().trim());
            }

            $text.toggleClass("d-none");
            $input.toggleClass("d-none");
        });

        $parent_tr.find(".editrow, .confirmrow").toggleClass("d-none");
        $(this).trigger("verifySave");
    });

    $(document).off("verifySave").on("verifySave", function() {
        var $table = $(document).find("#packagetypes");
        let enabled = $table.find("tr:not(.visually-hidden) .editrow.d-none").length === 0;
        $("#savepkgtypes").prop("disabled", !enabled);
    });
}

if ($("div#typesmgmt").length !== 0) {
    init_types_mgmt_page();
}
