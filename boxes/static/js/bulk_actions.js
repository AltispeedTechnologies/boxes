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
    window.initialize_async_select2("bulk_carrier", "/carriers/search", "#bulkEditModal");

    $("[data-bs-target=\"#bulkPrint\"]").on("click", function() {
        var row_ids = Array.from(window.selected_packages).join(",");
        window.open("/packages/label?ids=" + row_ids);
    });

    $("#checkoutbtn").click(function(event) {
        event.preventDefault();

        let packages_array = Array.from(window.selected_packages);
        let packages_payload = {"ids": packages_array};

        $.ajax({
            type: "POST",
            url: "/packages/checkout",
            headers: {"X-CSRFToken": window.csrf_token},
            data: packages_payload,
            success: function(response) {
                if (response.success) {
                    window.location.href = response.redirect_url;
                    window.display_error_message();
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    $("#bulkAddPicklistModal .btn-primary").on("click", function() {
        let picklist_id = $("#picklist-select-bulk").find(":selected").val();
        let packages_payload = {
            "ids": [...window.selected_packages],
            "picklist_id": picklist_id
        };

        $.ajax({
            type: "POST",
            url: "/packages/picklists/modify",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(packages_payload),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    // Handle the bulk check back in and out modal logic
    $("#bulkCheckBackInModal .btn-primary, #bulkCheckOutModal .btn-primary").on("click", function() {
        let url = $(this).closest(".modal").attr("id") === "bulkCheckBackInModal" ? "/packages/checkout/reverse" : "/packages/checkout";
        let packages = {"ids": [...window.selected_packages]};

        $.ajax({
            type: "POST",
            url: url,
            headers: {"X-CSRFToken": window.csrf_token},
            data: packages,
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    // Handle the bulk edit modal logic
    $('[data-bs-target="#bulkEditModal"]').on("click", function() {
        $("#bulkEditModal").find("#price").val("6.00");
        window.initialize_async_select2("carrier", "/carriers/search", "#bulkEditModal");
    });

    $("#bulkEditModal .btn-primary").on("click", function() {
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

        $.ajax({
            type: "POST",
            url: "/packages/update",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(payload),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    $("#bulkEditModal").modal("hide");
                    update_package_rows(price, carrier);
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    $("#bulkMoveModal .btn-primary").on("click", function() {
        let picklist_id = $("#picklist-select-bulk-move").find(":selected").val();
        var post_data = {
            ids: Array.from(window.selected_packages),
            picklist_id: Number(picklist_id)
        };

        $.ajax({
            type: "POST",
            url: "/packages/picklists/modify",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(post_data),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    $("#bulkRemoveModal .btn-primary").on("click", function() {
        var post_data = {
            ids: Array.from(window.selected_packages),
        };

        $.ajax({
            type: "POST",
            url: "/packages/picklists/remove",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(post_data),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });
}

$(document).ready(function() {
    window.picklist_total_functions++;

    $(document).on("picklistQueryDone", function(event, data) {
        $("#picklist-select-bulk").select2({
            data: data,
            dropdownParent: "#bulkAddPicklistModal",
            width: "100%"
        });
        $("#picklist-select-bulk-move").select2({
            data: data,
            dropdownParent: "#bulkMoveModal",
            width: "100%"
        });
    });

    $.ajax({
        url: "/modals/bulk",
        type: "GET",
        headers: {
            "X-CSRFToken": window.csrf_token
        },
        success: function(response) {
            $("#bulkModalContainer").html(response);
            setup_bulk_actions();
            $(document).trigger("picklistQuery");
        },
        error: function() {
            console.error("Error loading modals");
        }
    });
});

$(document).on("selectedPackagesUpdated", function(event) {
    var no_selected_packages = (window.selected_packages.size == 0);

    $("#bulkprintbtn").prop("disabled", no_selected_packages);
    $("#bulkeditbtn").prop("disabled", no_selected_packages);
    $("#bulkpicklistbtn").prop("disabled", no_selected_packages);
    $("#bulkpicklistmovebtn").prop("disabled", no_selected_packages);
    $("#bulkpicklistremovebtn").prop("disabled", no_selected_packages);
    $("#bulkcheckoutbtn").prop("disabled", no_selected_packages);
    $("#bulkcheckbackinbtn").prop("disabled", no_selected_packages);
});
