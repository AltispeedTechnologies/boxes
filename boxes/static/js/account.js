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

    if ($("input#billable").length === 1) {
        $("input#billable").off("change").on("change", function() {
            let $input = $(this);
            $input.prop("disabled", true);
            $("#savingiconbillable").show();

            let acct_payload = {billable: $(this).prop("checked")};
            let account_id = $(this).attr("data-id");

            window.ajax_request({
                type: "POST",
                url: "/accounts/" + account_id + "/update",
                payload: JSON.stringify(acct_payload),
                content_type: "application/json",
                on_success: function(response) {
                    $input.prop("disabled", false);
                    window.display_error_message();
                    $("#savingiconbillable").hide();
                    $("#successiconbillable").show();
                    setTimeout(function() {
                        $("#successiconbillable").fadeOut();
                    }, 1000);
                }
            });
        });
    }
}

window.manage_init_func("textarea#accountnotes", "account", init_account_page);
