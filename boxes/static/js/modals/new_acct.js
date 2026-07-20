/**
 * @file modals/new_acct.js
 * @description Modal workflow to create a new account (optional web login).
 * @see docs/api/javascript.md
 */

function new_acct() {
    var $modal = $("#createNewCustomerModal");
    var $webToggle = $("#create_web_account");
    var $webFields = $("#web-account-fields");

    $webToggle.off("change").on("change", function() {
        if ($(this).is(":checked")) {
            $webFields.show();
        } else {
            $webFields.hide();
        }
    });

    $modal.find(".btn-primary").off("click").on("click", function() {
        $("#savingiconnew").show();
        var $form = $("#userform");

        var form_data = {};
        $form.serializeArray().forEach(function(item) {
            form_data[item.name] = item.value;
        });
        // checkbox only present when checked via serialize; force boolean
        form_data.create_web_account = $webToggle.is(":checked");

        window.ajax_request({
            type: "POST",
            url: "/users/new",
            payload: JSON.stringify(form_data),
            content_type: "application/json",
            on_response: function() {
                $form.find(".is-invalid").removeClass("is-invalid");
                $("#savingiconnew").hide();
            },
            on_success: function(response) {
                if ($("#create_account_id").length === 0) { window.location.reload(); }

                var option = new Option(response.account_name, response.account_id, true, true);
                $("#create_account_id").append(option);
                $("#create_account_id").val(response.account_id).trigger("change");
                $modal.modal("hide");
            }
        });
    });
}

$(new_acct);
