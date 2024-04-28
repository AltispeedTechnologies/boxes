$(document).ready(function() {
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
