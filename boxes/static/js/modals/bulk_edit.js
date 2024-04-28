$(document).ready(function() {
    var package_data = {};

    $('[data-bs-target="#bulkEditModal"]').on("click", function () {
        $("#bulkEditModal").find("#price").val("6.00");
        window.initialize_async_select2("carrier", "/carriers/search", "#bulkEditModal");
    });

    $("#bulkEditModal .btn-primary").on("click", function() {
        let csrf_token = window.get_cookie("csrftoken");
        let price = $("#bulkEditModal").find("#price").val();
        let carrier_id = $("#bulkEditModal").find("#id_carrier_id").val();
        let carrier = $("#bulkEditModal").find("#id_carrier_id option:selected").text();

        var post_data = {
            ids: Array.from(window.selected_packages),
            values: {
                price: price,
                carrier_id: carrier_id,
            },
        };

        $.ajax({
            type: "POST",
            url: "/packages/update",
            headers: {"X-CSRFToken": csrf_token},
            data: JSON.stringify(post_data),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    window.selected_packages.forEach(function(package_id) {
                        var $tr = $('tr[data-row-id="' + package_id + '"]');
                        
                        $tr.find("td").each(function() {
                            var type = $(this).data("type");

                            if (type) {
                                if (type === "price") {
                                    $(this).text("$" + price);
                                } else if (type === "carrier" && carrier != "") {
                                    $(this).text(carrier.replace(" (Create new)", ""));
                                }
                            }
                        });
                    });

                    $("#bulkEditModal").modal("hide");
                } else {
                    console.error("Update failed:", response.errors ? response.errors.join("; ") : "Unknown error");
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });
});
