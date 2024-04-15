$(document).ready(function() {
    var package_data = {};

    $('[data-bs-target="#editModal"]').on("click", function () {
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
            if (type === "account") {
                package_data.account_id = $(this).data("id");
            }
        });

        $("#tracking_code").val(package_data.tracking_code);
        $("#price").val(package_data.price.replace("$", ""));
        $("#comments").val(package_data.comments);
    });

    $("#editModal").on("shown.bs.modal", function () {
        let csrf_token = window.get_cookie("csrftoken");

        window.initialize_async_select2("account", "/accounts/search", "#editModal");
        window.initialize_async_select2("carrier", "/carriers/search", "#editModal");

        var option = new Option(package_data.account, package_data.account_id, true, true);
        $("#id_account_id").append(option).trigger("change");

        $("#id_account_id").trigger({
            type: "select2:select",
            params: {
                data: { id: package_data.account_id, text: package_data.account }
            }
        });
    });
});
