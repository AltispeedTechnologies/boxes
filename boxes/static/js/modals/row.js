var row_id;

function setup_actions() {
    $(document).off("rowsUpdated").on("rowsUpdated", handle_updated_rows);

    $("[data-bs-target=\"#editModal\"]").off("click").on("click", init_edit_modal);

    $(document).on("click",
        "[data-bs-target=\"#print\"], " +
        "[data-bs-target=\"#addPicklistModal\"], " +
        "[data-bs-target=\"#checkBackInModal\"], " +
        "[data-bs-target=\"#checkOutModal\"], " +
        "[data-bs-target=\"#moveModal\"], " +
        "[data-bs-target=\"#removeModal\"]",
        function() {
            var tr = $(this).closest("tr");
            row_id = tr.data("row-id");

            if ($(this).data("bs-target") === "#print") {
                window.open("/packages/label?ids=" + row_id);
            } else if ($(this).data("bs-target") === "#moveModal") {
                var current_picklist = $(this).attr("data-picklist-id");
                $("#picklist-select").val(current_picklist).trigger("change");
            }
        }
    );

    $("#addPicklistModal .btn-primary").off("click").on("click", function() {
        event.preventDefault();
        let picklist_id = $("#picklist-select-row").find(":selected").val();
        let packages_payload = {
            "ids": [row_id],
            "picklist_id": picklist_id
        };

        window.ajax_request({
            type: "POST",
            url: "/picklists/modify",
            payload: JSON.stringify(packages_payload),
            content_type: "application/json",
            on_success: function() {
                window.location.reload();
            }
        });
    });

    $("#checkBackInModal .btn-primary").off("click").on("click", function() {
        let packages = {"ids": [row_id]};

        window.ajax_request({
            type: "POST",
            url: "/packages/checkout/reverse",
            payload: packages,
            on_success: function() {
                window.location.reload();
            }
        });
    });

    $("#checkOutModal .btn-primary").off("click").on("click", function() {
        let packages = {"ids": [row_id]};

        window.ajax_request({
            type: "POST",
            url: "/packages/checkout/submit",
            payload: packages,
            on_success: function() {
                window.location.reload();
            }
        });
    });


    $("#editModal .btn-primary").off("click").on("click", function() {
        var $tr = $("tr[data-row-id=\"" + row_id + "\"]");

        var tracking_code = $("#editModal").find("#edit_tracking_code").val();
        var price = $("#editModal").find("#edit_price").val();
        var comments = $("#editModal").find("#edit_comments").val();
        var inside = $("#editModal").find("#edit_inside").prop("checked");
        var account_id = $("#editModal").find("#edit_account_id").val();
        var carrier_id = $("#editModal").find("#edit_carrier_id").val();
        var package_type_id = $("#editModal").find("#edit_package_type_id").val();
        var carrier = $("#editModal").find("#edit_carrier_id").find(":selected").text();
        var account = $("#editModal").find("#edit_account_id").find(":selected").text();
        var package_type = $("#editModal").find("#edit_package_type_id").find(":selected").text();

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

        window.ajax_request({
            type: "POST",
            url: "/packages/" + row_id + "/update",
            payload: JSON.stringify(post_data),
            content_type: "application/json",
            on_success: function() {
                $tr.find("td").each(function() {
                    var type = $(this).data("type");
                    var new_text;

                    if (type) {
                        if (type === "price") {
                            new_text = "$" + post_data[type];
                        } else if (type === "inside") {
                            if (inside) {
                                const icon = "<i class=\"fas fa-check-circle text-warning\"></i>";
                                $(this).html(icon).attr("data-id", "True");
                            } else {
                                const icon = "<i class=\"fas fa-times-circle text-info\"></i>";
                                $(this).html(icon).attr("data-id", "False");
                            }
                            return;
                        } else if (type === "account") {
                            new_text = account;
                        } else if (type === "carrier") {
                            new_text = carrier;
                        } else if (type === "package_type") {
                            new_text = package_type;
                        } else {
                            new_text = post_data[type];
                        }

                        var $target = $(this).find("a").length ? $(this).find("a") : $(this);
                        $target.text(new_text);
                    }
                });

                $("#editModal").modal("hide");
            }
        });
    });

    $("#moveModal .btn-primary").off("click").on("click", function() {
        var picklist_id = $("#picklist-select").val();

        var post_data = {
            ids: [row_id],
            picklist_id: Number(picklist_id)
        };

        window.ajax_request({
            type: "POST",
            url: "/picklists/modify",
            payload: JSON.stringify(post_data),
            content_type: "application/json",
            on_success: function() {
                window.location.reload();
            }
        });
    });

    $("#removeModal .btn-primary").off("click").on("click", function() {
        const id_array = [row_id];

        // Prepare data for POST request
        var post_data = {
            ids: id_array
        };

        window.ajax_request({
            type: "POST",
            url: "/picklists/remove",
            payload: JSON.stringify(post_data),
            content_type: "application/json",
            on_success: function() {
                window.location.reload();
            }
        });
    });
}

function init_edit_modal(event) {
    let package_data = {};
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
        } else if (type === "inside") {
            package_data[type] = $(this).attr("data-id");
        }
    });

    $("#editModal").find("#edit_tracking_code").val(package_data.tracking_code);
    $("#editModal").find("#edit_price").val(package_data.price.replace("$", ""));
    $("#editModal").find("#edit_comments").val(package_data.comments);
    $("#editModal").find("#edit_inside").prop("checked", package_data.inside === "True");

    window.initialize_async_select2("edit_account_id", "/accounts/search", "#editModal");
    window.initialize_async_select2("edit_carrier_id", "/carriers/search", "#editModal");
    window.initialize_async_select2("edit_package_type_id", "/types/search", "#editModal");

    // Preload options into the various dropdowns
    /// account
    var acct_option = new Option(package_data.account, package_data.account_id, true, true);
    $("#editModal").find("#edit_account_id").append(acct_option).trigger("change");
    $("#editModal").find("#edit_account_id").trigger({
        type: "select2:select",
        params: {
            data: { id: package_data.account_id, text: package_data.account }
        }
    });

    /// carrier
    var carrier_option = new Option(package_data.carrier, package_data.carrier_id, true, true);
    $("#editModal").find("#edit_carrier_id").append(carrier_option).trigger("change");
    $("#editModal").find("#edit_carrier_id").trigger({
        type: "select2:select",
        params: {
            data: { id: package_data.carrier_id, text: package_data.carrier }
        }
    });

    /// type
    var type_option = new Option(package_data.package_type, package_data.package_type_id, true, true);
    $("#editModal").find("#edit_package_type_id").append(type_option).trigger("change");
    $("#editModal").find("#edit_package_type_id").trigger({
        type: "select2:select",
        params: {
            data: { id: package_data.package_type_id, text: package_data.package_type }
        }
    });
}

function handle_updated_rows() {
    $("[data-bs-target=\"#editModal\"]").off("click");
    $("[data-bs-target=\"#editModal\"]").on("click", init_edit_modal);
}

function row_modals() {
    window.picklist_data().then(function(data) {
        let picklist_data = data;

        $("#picklist-select").select2({
            data: picklist_data,
            dropdownParent: "#moveModal",
            width: "100%"
        });

        $("#picklist-select-row").select2({
            data: picklist_data,
            dropdownParent: "#addPicklistModal",
            width: "100%"
        });

        window.select2properheight("#picklist-select");
        window.select2properheight("#picklist-select-row");
    });
    setup_actions();
}

if ($("#editModal").length !== 0) {
    row_modals();
}
