/**
 * @file account.js
 * @description Staff account detail page interactions (comments save, etc.).
 * @see docs/api/javascript.md
 */

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

    if ($("#postwaiver").length === 1) {
        $("#postwaiver").off("click").on("click", function() {
            let account_id = $("#feewaiver").attr("data-account-id");
            let amount = $("#waiver_amount").val().trim();
            let description = $("#waiver_description").val().trim() || "Fee waiver";
            if (!amount) {
                window.display_error_message("Amount is required");
                return;
            }
            $("#savingiconwaiver").show();
            window.ajax_request({
                type: "POST",
                url: "/accounts/" + account_id + "/waiver",
                payload: JSON.stringify({amount: amount, description: description}),
                content_type: "application/json",
                on_success: function(response) {
                    $("#savingiconwaiver").hide();
                    $("#successiconwaiver").show();
                    setTimeout(function() {
                        $("#successiconwaiver").fadeOut();
                        window.location.reload();
                    }, 800);
                }
            });
        });
    }
}

$(init_account_page);
