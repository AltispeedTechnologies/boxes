function init_account_page() {
    $("#accountnotes").off("input").on("input", window.debounce(function() {
        $("#savingnotes").removeClass("d-none");
        let account_id = $(this).attr("data-id");

        new_comments = $(this).val();
        let payload = JSON.stringify({"comments": new_comments});

        window.ajax_request({
            type: "POST",
            url: "/accounts/" + account_id + "/update",
            payload: payload,
            on_success: function(response) {
                $("#savingnotes").addClass("d-none");
                $("#donesavingnotes").show();
                $("#donesavingnotes").fadeOut(2000);
            }
        });
    }, 500));
}

window.manage_init_func("textarea#accountnotes", "account", init_account_page);
