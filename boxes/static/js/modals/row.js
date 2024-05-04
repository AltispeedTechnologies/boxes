var row_id;

function setup_actions() {
    $(document).on("rowsUpdated", handle_updated_rows);

    $('[data-bs-target="#editModal"]').on("click", init_edit_modal);

    $(document).on("click", 
        '[data-bs-target="#print"], ' +
        '[data-bs-target="#addPicklistModal"], ' +
        '[data-bs-target="#checkBackInModal"], ' +
        '[data-bs-target="#checkOutModal"], ' +
        '[data-bs-target="#moveModal"], ' +
        '[data-bs-target="#removeModal"]', 
        function() {
            var tr = $(this).closest("tr");
            row_id = tr.data("row-id");

            if ($(this).data("bs-target") === "#print") {
                window.open("/packages/label?ids=" + row_id);
            }
        }
    );

    $("#addPicklistModal .btn-primary").on("click", function() {
        event.preventDefault();
        let picklist_id = $("#picklist-select-row").find(":selected").val();
        let packages_payload = {
            "ids": [row_id],
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
                    console.log(response.errors);
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    $("#checkBackInModal .btn-primary").on("click", function() {
        let packages = {"ids": [row_id]};

        $.ajax({
            type: "POST",
            url: "/packages/checkout/reverse",
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

    $("#checkOutModal .btn-primary").on("click", function() {
        let packages = {"ids": [row_id]};

        $.ajax({
            type: "POST",
            url: "/packages/checkout",
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


    $("#editModal .btn-primary").on("click", function() {
        var $tr = $('tr[data-row-id="' + row_id + '"]');

        var tracking_code = $("#editModal").find("#tracking_code").val();
        var price = $("#editModal").find("#price").val();
        var comments = $("#editModal").find("#comments").val();
        var inside = $("#editModal").find("#id_inside").prop("checked");
        var account_id = $("#editModal").find("#id_account_id").val();
        var account = $("#editModal").find("#id_account_id option:selected").text();
        var carrier_id = $("#editModal").find("#id_carrier_id").val();
        var carrier = $("#editModal").find("#id_carrier_id option:selected").text();
        var package_type_id = $("#editModal").find("#id_package_type_id").val();
        var package_type = $("#editModal").find("#id_package_type_id option:selected").text();

        // Prepare data for POST request
        var post_data = {
            tracking_code: tracking_code,
            price: price,
            comments: comments,
            account_id: account_id,
            carrier_id: carrier_id,
            package_type_id: package_type_id,
            inside: inside
        };

        $.ajax({
            type: "POST",
            url: "/packages/" + row_id + "/update",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(post_data),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    $tr.find("td").each(function() {
                        var type = $(this).data("type");

                        if (type) {
                            if (type === "price") {
                                $(this).text("$" + post_data[type]);
                            } else if (type === "account") {
                                $(this).text(account.replace(" (Create new)", ""));
                            } else if (type === "carrier") {
                                $(this).text(carrier.replace(" (Create new)", ""));
                            } else if (type === "package_type") {
                                $(this).text(package_type.replace(" (Create new)", ""));
                            } else {
                                $(this).text(post_data[type]);
                            }
                        }
                    });

                    $("#editModal").modal("hide");
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

    $("#moveModal .btn-primary").on("click", function() {
        var picklist_id = $("#picklist-select").val();

        var post_data = {
            ids: [row_id],
            picklist_id: Number(picklist_id)
        };
        console.log(post_data);

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
                    console.error("Move to picklist failed:", response.errors.join("; "));
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    $("#removeModal .btn-primary").on("click", function() {
        const id_array = [row_id];

        // Prepare data for POST request
        var post_data = {
            ids: id_array
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

function init_edit_modal(event) {
    package_data = {};
    var tr = $(event.target).closest("tr");
    row_id = tr.data("row-id");

    // Only grab packages with a defined data type
    tr.find("td[data-type]").each(function() {
        var text = $(this).text().trim();
        var type = $(this).data("type");
        if (text !== "") {
            package_data[type] = text;
        }

        // Extra data
        if (type === "account" || type === "carrier" || type === "package_type") {
            package_data[type + "_id"] = $(this).data("id");
        }
    });

    $("#tracking_code").val(package_data.tracking_code);
    $("#editModal").find("#price").val(package_data.price.replace("$", ""));
    $("#comments").val(package_data.comments);

    window.initialize_async_select2("account", "/accounts/search", "#editModal");
    window.initialize_async_select2("carrier", "/carriers/search", "#editModal");
    window.initialize_async_select2("package_type", "/types/search", "#editModal");

    // Preload options into the various dropdowns
    /// account
    var acct_option = new Option(package_data.account, package_data.account_id, true, true);
    $("#editModal").find("#id_account_id").append(acct_option).trigger("change");
    $("#editModal").find("#id_account_id").trigger({
        type: "select2:select",
        params: {
            data: { id: package_data.account_id, text: package_data.account }
        }
    });

    /// carrier
    var carrier_option = new Option(package_data.carrier, package_data.carrier_id, true, true);
    $("#editModal").find("#id_carrier_id").append(carrier_option).trigger("change");
    $("#editModal").find("#id_carrier_id").trigger({
        type: "select2:select",
        params: {
            data: { id: package_data.carrier_id, text: package_data.carrier }
        }
    });

    /// type
    var type_option = new Option(package_data.package_type, package_data.package_type_id, true, true);
    $("#editModal").find("#id_package_type_id").append(type_option).trigger("change");
    $("#editModal").find("#id_package_type_id").trigger({
        type: "select2:select",
        params: {
            data: { id: package_data.package_type_id, text: package_data.package_type }
        }
    });
}

function handle_updated_rows() {
    $('[data-bs-target="#editModal"]').off("click");
    $('[data-bs-target="#editModal"]').on("click", init_edit_modal);
}

$(document).ready(function() {
    $(document).trigger("wantPicklistQuery");

    $(document).on("picklistQueryDone", function(event, data) {
        if (typeof picklist_data !== "undefined") {
            $("#picklist-select").select2({
                data: picklist_data,
                dropdownParent: "#moveModal",
                width: "100%"
            });
        } else {
            $("#picklist-select-row").select2({
                data: data,
                dropdownParent: "#addPicklistModal",
                width: "100%"
            });

            $("#picklist-select").select2({
                data: data,
                dropdownParent: "#moveModal",
                width: "100%"
            });
        }
    });

    $.ajax({
        url: "/modals/actions",
        type: "GET",
        headers: {
            "X-CSRFToken": window.csrf_token
        },
        success: function(response) {
            $("#modalContainer").html(response);
            setup_actions();
            $(document).trigger("picklistQuery");
        },
        error: function() {
            console.error("Error loading modals");
        }
    });

});
