$(document).ready(function() {
    var package_data = {};
    var row_id = null;

    $('[data-bs-target="#editModal"]').on("click", function () {
        let csrf_token = window.get_cookie("csrftoken");
        package_data = {};
        row_id = $(this).data("row-id");
        var tr = $(this).closest("tr");

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

        console.log(package_data);

        $("#tracking_code").val(package_data.tracking_code);
        $("#editModal").find("#price").val(package_data.price.replace("$", ""));
        $("#comments").val(package_data.comments);

        window.initialize_async_select2("account", "/accounts/search", "#editModal");
        window.initialize_async_select2("carrier", "/carriers/search", "#editModal");
        window.initialize_async_select2("type", "/types/search", "#editModal");

        // Preload options into the various dropdowns
        /// account
        var acct_option = new Option(package_data.account, package_data.account_id, true, true);
        $("#id_account_id").append(acct_option).trigger("change");
        $("#id_account_id").trigger({
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
        $("#id_package_type_id").append(type_option).trigger("change");
        $("#id_package_type_id").trigger({
            type: "select2:select",
            params: {
                data: { id: package_data.package_type_id, text: package_data.package_type }
            }
        });
    });

    $("#editModal .btn-primary").on("click", function() {
        let csrf_token = window.get_cookie("csrftoken");
        var $tr = $('tr[data-row-id="' + row_id + '"]');

        var tracking_code = $("#editModal").find("#tracking_code").val();
        var price = $("#editModal").find("#price").val();
        var comments = $("#editModal").find("#comments").val();
        var inside = $("#id_inside").prop("checked");
        var account_id = $("#id_account_id").val();
        var account = $("#id_account_id option:selected").text();
        var carrier_id = $("#editModal").find("#id_carrier_id").val();
        var carrier = $("#editModal").find("#id_carrier_id option:selected").text();
        var package_type_id = $("#id_package_type_id").val();
        var package_type = $("#id_package_type_id option:selected").text();

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
            headers: {"X-CSRFToken": csrf_token},
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
});
