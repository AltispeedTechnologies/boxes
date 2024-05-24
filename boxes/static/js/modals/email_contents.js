$(document).ready(function() {
    $("[data-bs-target=\"#showEmailModal\"]").on("click", function() {
        $("#emailcontents").html("");
        $("#loadingstatus").show();

        let sent_email_id = $(this).closest("tr").attr("data-id");

        $.ajax({
            url: "/emails/" + sent_email_id + "/contents",
            type: "GET",
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            success: function(response) {
                $("#loadingstatus").hide();
                $("#emailcontents").html(response.contents);
            }
        });
    });
});