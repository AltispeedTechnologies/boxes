function email_contents() {
    $("[data-bs-target=\"#showEmailModal\"]").off("click").on("click", function() {
        $("#emailcontents").html("");
        $("#showEmailModalLabel").text("Loading...");
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
                $("#showEmailModalLabel").text(response.subject);
            }
        });
    });
}

if ($("#showEmailModal").length !== 0) {
    email_contents();
}
