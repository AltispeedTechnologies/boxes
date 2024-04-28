$(document).ready(function() {
    $("#editaccountdesc").click(function(event) {
        event.preventDefault();
        $("#descdisplay").addClass("d-none");
        $("#descedit").removeClass("d-none");

        current_desc = $("#accountdesc").text();
        $("#accountdesceditbox").val(current_desc);
    });

    $("#saveaccountdesc").click(function(event) {
        event.preventDefault();
        var csrf = window.get_cookie("csrftoken");
        let account_id = $("#saveaccountdesc").data("accountId");

        let new_desc = $("#accountdesceditbox").val();
        let payload = JSON.stringify({"description": new_desc});

        $.ajax({
            type: "POST",
            url: "/accounts/" + account_id + "/update",
            headers: {
                "X-CSRFToken": csrf
            },
            data: payload,
            success: function(response) {
                if (response.success) {
                    $("#accountdesc").text(new_desc);
                    $("#descedit").addClass("d-none");
                    $("#descdisplay").removeClass("d-none");
                } else {
                    console.log(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.log(error);
            }
        });
    });
});
