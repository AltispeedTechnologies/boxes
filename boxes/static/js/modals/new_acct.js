/**
 * @file modals/new_acct.js
 * @description Modal workflow to create a user and/or billing account, or send a signup invite.
 * @see docs/api/javascript.md
 */

function new_acct_portal_mode() {
    return $('input[name="portal_mode"]:checked').val() || "none";
}

function new_acct_sync_fields() {
    var mode = new_acct_portal_mode();
    var $webFields = $("#web-account-fields");
    var $inviteHint = $("#invite-hint");
    if (mode === "credentials") {
        $webFields.show();
        $inviteHint.hide();
    } else if (mode === "invite") {
        $webFields.hide();
        $inviteHint.show();
    } else {
        $webFields.hide();
        $inviteHint.hide();
    }
}

function new_acct() {
    var $modal = $("#createNewCustomerModal");
    if (!$modal.length) {
        return;
    }

    // Users page prefers login-only by default
    $modal.on("show.bs.modal", function() {
        var defCreate = $modal.data("default-create-account");
        if (defCreate === 0 || defCreate === "0") {
            $("#create_account").prop("checked", false);
        } else {
            $("#create_account").prop("checked", true);
        }
        $("#portal_none").prop("checked", true);
        new_acct_sync_fields();
        $modal.find(".is-invalid").removeClass("is-invalid");
    });

    $('input[name="portal_mode"]').off("change.newacct").on("change.newacct", new_acct_sync_fields);

    $modal.find(".btn-primary").off("click.newacct").on("click.newacct", function() {
        $("#savingiconnew").show();
        var $form = $("#userform");
        var form_data = {};
        $form.serializeArray().forEach(function(item) {
            form_data[item.name] = item.value;
        });

        var mode = new_acct_portal_mode();
        form_data.create_account = $("#create_account").is(":checked");
        form_data.create_web_account = mode === "credentials";
        form_data.send_invite = mode === "invite";
        if (mode !== "credentials") {
            delete form_data.username;
            delete form_data.password;
            delete form_data.password2;
        }
        delete form_data.portal_mode;

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
                if (response.invite) {
                    var msg = response.message || "Invitation created.";
                    if (response.signup_path && !response.email_sent) {
                        msg += " Link: " + response.signup_path;
                    }
                    if (window.alert) {
                        window.alert(msg);
                    }
                    if ($("#usermgmt").length) {
                        window.location.reload();
                        return;
                    }
                    $modal.modal("hide");
                    return;
                }

                // Check-in flow: select the new account in the package form
                if ($("#create_account_id").length && response.account_id) {
                    var option = new Option(response.account_name, response.account_id, true, true);
                    $("#create_account_id").append(option);
                    $("#create_account_id").val(response.account_id).trigger("change");
                    $modal.modal("hide");
                    return;
                }

                // Users management: go to the new user
                if (response.user_id && $("#usermgmt").length) {
                    window.location.href = "/users/" + response.user_id + "/edit";
                    return;
                }

                window.location.reload();
            }
        });
    });
}

$(new_acct);
