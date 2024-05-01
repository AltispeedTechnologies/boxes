$(document).ready(function() {
    var package_data = {};
    var row_id = null;

    $('[data-bs-target="#checkOutModal"]').on("click", function () {
        var tr = $(this).closest("tr");
        row_id = tr.data("row-id");
    });

    $("#checkOutModal .btn-primary").on("click", function() {
        let csrf_token = window.get_cookie("csrftoken");
        let packages = {"ids": [row_id]};

        $.ajax({
            type: "POST",
            url: "/packages/checkout",
            headers: {"X-CSRFToken": csrf_token},
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
});
