$(document).ready(function() {
    var csrf = window.get_cookie("csrftoken");

    $("#editaccountdesc").click(function(event) {
        event.preventDefault();
        $("#descdisplay").addClass("d-none");
        $("#descedit").removeClass("d-none");

        current_desc = $("#accountdesc").text();
        $("#accountdesceditbox").val(current_desc);
    });

    $("#saveaccountdesc").click(function(event) {
        event.preventDefault();
        let account_id = $("#saveaccountdesc").data("accountId");

        let new_name = $("#accountdesceditbox").val();
        let payload = JSON.stringify({"name": new_name});

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
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.log(error);
            }
        });
    });

    $("#accountnotes").on("input", window.debounce(function() {
        $("#savingnotes").removeClass("d-none");
        let account_id = $("#saveaccountdesc").data("accountId");

        new_comments = $(this).val();
        let payload = JSON.stringify({"comments": new_comments});

        $.ajax({
            type: "POST",
            url: "/accounts/" + account_id + "/update",
            headers: {
                "X-CSRFToken": csrf
            },
            data: payload,
            success: function(response) {
                if (response.success) {
                    $("#savingnotes").addClass("d-none");
                    $("#donesavingnotes").show();
                    $("#donesavingnotes").fadeOut(2000);
                } else {
                    //window.display_error_message(response.errors);
                    console.log(response);
                }
            },
            error: function(xhr, status, error) {
                console.log(error);
            }
        });
    }, 500));
});
