$(document).ready(function() {
    $("#bulkCheckBackInModal .btn-primary").on("click", function() {
        let csrf_token = window.get_cookie("csrftoken");
        let packages = {"ids": [...window.selected_packages]};

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
