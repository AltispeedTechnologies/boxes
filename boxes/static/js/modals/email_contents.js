function email_contents() {
    $("[data-bs-target=\"#showEmailModal\"]").off("click").on("click", function() {
        $("#emailcontents").html("");
        $("#showEmailModalLabel").text("Loading...");
        $("#loadingstatus").show();

        let sent_email_id = $(this).closest("tr").attr("data-id");

        window.ajax_request({
            type: "GET",
            url: "/emails/" + sent_email_id + "/contents",
            on_success: function(response) {
                $("#loadingstatus").hide();
                $("#emailcontents").html(response.contents);
                $("#showEmailModalLabel").text(response.subject);
            }
        });
    });
}

window.manage_init_func("#showEmailModal", "email_contents", email_contents);
