$(document).ready(function() {
    let csrf_token = window.get_cookie("csrftoken");

    $("[data-bs-target=\"#bulkPrint\"]").on("click", function() {
        var row_ids = Array.from(window.selected_packages).join(",");
        window.open("/packages/label?ids=" + row_ids);
    });

    $("#checkoutbtn").click(function(event) {
        event.preventDefault();

        let csrf_token = window.get_cookie("csrftoken");
        let packages_array = Array.from(window.selected_packages);
        let packages_payload = {"ids": packages_array};

        $.ajax({
            type: "POST",
            url: "/packages/checkout",
            headers: {"X-CSRFToken": csrf_token},
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
});

$(document).on("selectedPackagesUpdated", function(event) {
    var no_selected_packages = (window.selected_packages.size == 0);

    $("#bulkprintbtn").prop("disabled", no_selected_packages);
    $("#bulkeditbtn").prop("disabled", no_selected_packages);
});
