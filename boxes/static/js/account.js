$(document).ready(function() {
    $("#accountnotes").on("input", window.debounce(function() {
        $("#savingnotes").removeClass("d-none");
        let account_id = $(this).attr("data-id");

        new_comments = $(this).val();
        let payload = JSON.stringify({"comments": new_comments});

        $.ajax({
            type: "POST",
            url: "/accounts/" + account_id + "/update",
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            data: payload,
            success: function(response) {
                if (response.success) {
                    $("#savingnotes").addClass("d-none");
                    $("#donesavingnotes").show();
                    $("#donesavingnotes").fadeOut(2000);
                } else {
                    window.display_error_message(response.errors);
                }
            }
        });
    }, 500));
});
