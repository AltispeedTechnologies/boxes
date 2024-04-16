$(document).ready(function() {
    var package_data = {};

    $('[data-bs-target="#editModal"]').on("click", function () {
        let csrf_token = window.get_cookie("csrftoken");
        package_data = {};
        var row_id = $(this).data("row-id");
        var tr = $(this).closest("tr");

        // Only grab packages with a defined data type
        tr.find("td[data-type]").each(function() {
            var text = $(this).text().trim();
            var type = $(this).data("type");
            if (text !== "") {
                package_data[type] = text;
                console.log(type + " - " + text);
            }

            // Extra data
            if (type === "account" || type === "carrier" || type === "package_type") {
                package_data[type + "_id"] = $(this).data("id");
                console.log(package_data);
            }
        });

        $("#tracking_code").val(package_data.tracking_code);
        $("#price").val(package_data.price.replace("$", ""));
        $("#comments").val(package_data.comments);

        window.initialize_async_select2("account", "/accounts/search", "#editModal");
        window.initialize_async_select2("carrier", "/carriers/search", "#editModal");
        window.initialize_async_select2("type", "/types/search/", "#editModal");

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
        $("#id_carrier_id").append(carrier_option).trigger("change");
        $("#id_carrier_id").trigger({
            type: "select2:select",
            params: {
                data: { id: package_data.carrier_id, text: package_data.carrier }
            }
        });

        /// type
        var type_option = new Option(package_data.package_type, package_data.package_type_id, true, true);
        $("#id_type_id").append(type_option).trigger("change");
        $("#id_type_id").trigger({
            type: "select2:select",
            params: {
                data: { id: package_data.package_type_id, text: package_data.package_type }
            }
        });
    });
});
