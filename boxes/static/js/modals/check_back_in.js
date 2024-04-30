$(document).ready(function() {
    var package_data = {};
    var row_id = null;

    $('[data-bs-target="#checkBackInModal"]').on("click", function () {
        row_id = $(this).data("row-id");
    });

    $("#checkBackInModal .btn-primary").on("click", function() {
        let csrf_token = window.get_cookie("csrftoken");
        let packages = {"ids": [row_id]};

        $.ajax({
            type: "POST",
            url: "/packages/checkout/reverse",
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
