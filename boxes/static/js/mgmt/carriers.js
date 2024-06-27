function init_carrier_mgmt_page() {
    let new_type_id = 0;

    $("#addcarrier").off("click").on("click", function() {
        let new_row = $(".visually-hidden")
            .clone()
            .removeClass("visually-hidden")
            .attr("data-id", "NEW_" + ++new_type_id);

        $(".visually-hidden").before(new_row);
        $(this).trigger("verifySave");
    });

    $("#savecarriers").off("click").on("click", function() {
        $("#savingicon").show();
        var $table = $(document).find("#carriers");

        let payload = {};

        $table.find("tr:not(.visually-hidden)").each(function() {
            let data_id = $(this).attr("data-id");
            let name = $(this).find("td[data-type=\"name\"] span.text").text().trim();
            let phone_number = $(this).find("td[data-type=\"phone_number\"] span.text").text().trim();
            let website = $(this).find("td[data-type=\"website\"] span.text").text().trim();
            payload[data_id] = {name: name, phone_number: phone_number, website: website};
        });

        window.ajax_request({
            type: "POST",
            url: "/mgmt/packages/carriers/update",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function(response) {
                $.each(response.updated_carriers, function(key, new_id) {
                    $table.find("tr[data-id=\"" + key + "\"]").attr("data-id", new_id);
                });

                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
            }
        });
    });

    $("#carriers").off("input", "input.form-control").on("input", "input.form-control", function() {
        var row = $(this).closest("tr");
        var confirm_button = row.find(".confirmrow");

        row.find("input.form-control").each(function() {
            if ($(this).hasClass("name")) {
                $(this).toggleClass("is-invalid", $(this).val().trim() === "");
            }
        });

        var disabled = row.find("input.name").val().trim() === "";

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
        var $table = $(document).find("#carriers");
        let enabled = $table.find("tr:not(.visually-hidden) .editrow.d-none").length === 0;
        $("#savecarriers").prop("disabled", !enabled);
    });
}

window.manage_init_func("div#carriermgmt", "carriers", init_carrier_mgmt_page);
