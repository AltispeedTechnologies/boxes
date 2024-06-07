function update_package_rows(price, carrier) {
    window.selected_packages.forEach(function(package_id) {
        var $tr = $('tr[data-row-id="' + package_id + '"]');
        $tr.find("td").each(function() {
            var type = $(this).data("type");
            if (type === "price") {
                $(this).text("$" + price);
            } else if (type === "carrier" && carrier != "") {
                $(this).text(carrier);
            }
        });
    });
    window.display_error_message();
}

function setup_bulk_actions() {
    window.picklist_data().then(function(data) {
        let picklist_data = data;

        $("#picklist-select-bulk").select2({
            data: picklist_data,
            dropdownParent: "#bulkAddPicklistModal",
            width: "100%"
        });

        $("#picklist-select-bulk-move").select2({
            data: picklist_data,
            dropdownParent: "#bulkMoveModal",
            width: "100%"
        });

        window.select2properheight("#picklist-select-bulk");
        window.select2properheight("#picklist-select-bulk-move");
    });

    window.initialize_async_select2("bulk_carrier", "/carriers/search", "#bulkEditModal");

    $("[data-bs-target=\"#bulkPrint\"]").off("click").on("click", function() {
        var row_ids = Array.from(window.selected_packages).join(",");
        window.open("/packages/label?ids=" + row_ids);
    });

    $("#bulkCheckOutModal .btn-primary").off("click").on("click", function() {
        let packages_array = Array.from(window.selected_packages);
        let packages_payload = {"ids": packages_array};

        window.ajax_request({
            type: "POST",
            url: "/packages/checkout/submit",
            payload: packages_payload,
            on_success: function(response) {
                window.location.reload();
            }
        });
    });

    $("#bulkAddPicklistModal .btn-primary").off("click").on("click", function() {
        let picklist_id = $("#picklist-select-bulk").find(":selected").val();
        let packages_payload = {
            "ids": [...window.selected_packages],
            "picklist_id": picklist_id
        };

        window.ajax_request({
            type: "POST",
            url: "/picklists/modify",
            payload: JSON.stringify(packages_payload),
            content_type: "application/json",
            on_success: function(response) {
                window.location.reload();
            }
        });
    });

    // Handle the bulk check back in and out modal logic
    $("#bulkCheckBackInModal .btn-primary, #bulkCheckOutModal .btn-primary").off("click").on("click", function() {
        let url = $(this).closest(".modal").attr("id") === "bulkCheckBackInModal" ? "/packages/checkout/reverse" : "/packages/checkout/submit";
        let packages = {"ids": [...window.selected_packages]};

        window.ajax_request({
            type: "POST",
            url: url,
            payload: packages,
            on_success: function(response) {
                window.location.reload();
            }
        });
    });

    // Handle the bulk edit modal logic
    $('[data-bs-target="#bulkEditModal"]').off("click").on("click", function() {
        $("#bulkEditModal").find("#price").val("6.00");
        window.initialize_async_select2("carrier", "/carriers/search", "#bulkEditModal");
    });

    $("#bulkEditModal .btn-primary").off("click").on("click", function() {
        let price = $("#bulkEditModal").find("#price").val();
        let carrier_id = $("#bulkEditModal").find("#id_bulk_carrier_id").val();
        let carrier = $("#bulkEditModal").find("#id_bulk_carrier_id option:selected").text();
        if (typeof window.no_ledger === "undefined") { window.no_ledger = false; }

        var payload = {
            ids: Array.from(window.selected_packages),
            values: {
                price: price,
                carrier_id: carrier_id,
            },
            no_ledger: window.no_ledger
        };

        window.ajax_request({
            type: "POST",
            url: "/packages/update",
            payload: JSON.stringify(payload),
            on_success: function(response) {
                $("#bulkEditModal").modal("hide");
                update_package_rows(price, carrier);
            }
        });
    });

    $("#bulkMoveModal .btn-primary").off("click").on("click", function() {
        let picklist_id = $("#picklist-select-bulk-move").find(":selected").val();
        var post_data = {
            ids: Array.from(window.selected_packages),
            picklist_id: Number(picklist_id)
        };

        window.ajax_request({
            type: "POST",
            url: "/picklists/modify",
            payload: JSON.stringify(post_data),
            content_type: "application/json",
            on_success: function(response) {
                window.location.reload();
            }
        });
    });

    $("#bulkRemoveModal .btn-primary").off("click").on("click", function() {
        var post_data = {
            ids: Array.from(window.selected_packages),
        };

        window.ajax_request({
            type: "POST",
            url: "/picklists/remove",
            payload: JSON.stringify(post_data),
            content_type: "application/json",
            on_success: function(response) {
                window.location.reload();
            }
        });
    });
}

$(document).off("selectedPackagesUpdated").on("selectedPackagesUpdated", function(event) {
    var no_selected_packages = (window.selected_packages.size == 0);

    $("#bulkprintbtn").prop("disabled", no_selected_packages);
    $("#bulkeditbtn").prop("disabled", no_selected_packages);
    $("#bulkpicklistbtn").prop("disabled", no_selected_packages);
    $("#bulkpicklistmovebtn").prop("disabled", no_selected_packages);
    $("#bulkpicklistremovebtn").prop("disabled", no_selected_packages);
    $("#bulkcheckoutbtn").prop("disabled", no_selected_packages);
    $("#bulkcheckbackinbtn").prop("disabled", no_selected_packages);
    $("#bulkactionsdropdown").toggle(!no_selected_packages);
});

if ($("div#bulkactions").length !== 0) {
    setup_bulk_actions();
}
