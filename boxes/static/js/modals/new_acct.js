/**
 * @file modals/new_acct.js
 * @description Create customer / user / invite modal with client-side validation
 *              and clear "what will be created" summary.
 * @see docs/api/javascript.md
 */

function new_acct_portal_mode() {
    return $('input[name="portal_mode"]:checked').val() || "none";
}

function new_acct_clear_feedback() {
    var $form = $("#userform");
    $form.find(".is-invalid").removeClass("is-invalid");
    $form.find(".invalid-feedback").text("");
    var $alert = $("#new-customer-alert");
    $alert.addClass("d-none").removeClass("alert-danger alert-success alert-warning").text("");
}

function new_acct_show_alert(kind, message) {
    var $alert = $("#new-customer-alert");
    $alert.removeClass("d-none alert-danger alert-success alert-warning");
    $alert.addClass("alert-" + (kind || "danger"));
    $alert.text(message || "");
}

function new_acct_set_field_error(field, message) {
    var $input = $("#" + field);
    if (!$input.length) {
        return;
    }
    $input.addClass("is-invalid");
    var $fb = $input.siblings(".invalid-feedback");
    if ($fb.length) {
        $fb.text(message || "Invalid");
    }
}

function new_acct_apply_form_errors(form_errors) {
    if (!form_errors) {
        return;
    }
    var messages = [];
    $.each(form_errors, function(field, errors) {
        var list = $.isArray(errors) ? errors : [errors];
        var msg = list.join(" ");
        if (field === "__all__" || field === "non_field") {
            messages.push(msg);
        } else {
            new_acct_set_field_error(field, msg);
            messages.push((field.replace(/_/g, " ")) + ": " + msg);
        }
    });
    if (messages.length) {
        new_acct_show_alert("danger", messages.join(" "));
    }
}

function new_acct_update_summary() {
    var createAccount = $("#create_account").is(":checked");
    var mode = new_acct_portal_mode();
    var parts = [];
    if (createAccount) {
        parts.push("a billing account (parcels and balance)");
    }
    if (mode === "credentials") {
        parts.push("an active portal login with the username and password you enter");
    } else if (mode === "invite") {
        parts.push("a sign-up invitation email (customer registers via link only)");
        if (createAccount) {
            parts.push("the new login will be linked to the billing account when they finish sign-up");
        }
    } else if (createAccount) {
        parts.push("no portal login yet (inactive placeholder membership for staff tools)");
    }
    if (!createAccount && mode === "none") {
        $("#new-customer-summary-text").text(
            "Nothing valid yet — turn on billing account and/or choose credentials or invite."
        );
        return;
    }
    if (!createAccount && mode === "credentials") {
        parts = ["a portal login only (no billing account until you link one later)"];
    }
    if (!createAccount && mode === "invite") {
        parts = ["a sign-up invitation only (no billing account until they register or you link one)"];
    }
    $("#new-customer-summary-text").text(parts.join("; ") + ".");

    // Required markers
    $(".req-mark[data-req='email']").toggleClass("d-none", mode !== "invite");
    // Name required for account or credentials (invite can fall back to email local-part server-side,
    // but first name is still strongly preferred)
    var nameRequired = createAccount || mode === "credentials" || mode === "invite";
    $(".req-mark[data-req='name']").toggleClass("d-none", !nameRequired);
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
    new_acct_update_summary();
}

function new_acct_client_validate() {
    new_acct_clear_feedback();
    var createAccount = $("#create_account").is(":checked");
    var mode = new_acct_portal_mode();
    var firstName = ($("#first_name").val() || "").trim();
    var email = ($("#email").val() || "").trim();
    var username = ($("#username").val() || "").trim();
    var password = $("#password").val() || "";
    var password2 = $("#password2").val() || "";
    var ok = true;
    var messages = [];

    if (!createAccount && mode === "none") {
        messages.push(
            "Choose at least one action: create a billing account, create login credentials, or send a sign-up invitation."
        );
        ok = false;
    }

    if ((createAccount || mode === "credentials") && !firstName && mode !== "invite") {
        new_acct_set_field_error("first_name", "First name is required.");
        messages.push("First name is required.");
        ok = false;
    }

    if (mode === "invite") {
        if (!email) {
            new_acct_set_field_error("email", "Email is required for invitations.");
            messages.push("Email is required to send a sign-up invitation.");
            ok = false;
        }
        if (!firstName) {
            // soft: server can use email local-part; still warn in summary
            new_acct_set_field_error("first_name", "First name is recommended for the invitation.");
        }
    }

    if (mode === "credentials") {
        if (!username) {
            new_acct_set_field_error("username", "Username is required.");
            messages.push("Username is required for portal login.");
            ok = false;
        }
        if (!password) {
            new_acct_set_field_error("password", "Password is required.");
            messages.push("Password is required for portal login.");
            ok = false;
        }
        if (password && password2 && password !== password2) {
            new_acct_set_field_error("password2", "Passwords do not match.");
            messages.push("Passwords do not match.");
            ok = false;
        }
        if (password && !password2) {
            new_acct_set_field_error("password2", "Confirm the password.");
            messages.push("Confirm the password.");
            ok = false;
        }
        if (!firstName) {
            new_acct_set_field_error("first_name", "First name is required.");
            messages.push("First name is required.");
            ok = false;
        }
    }

    if (!ok && messages.length) {
        new_acct_show_alert("danger", messages.join(" "));
    }
    return ok;
}

function new_acct_build_payload() {
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
    return form_data;
}

function new_acct() {
    var $modal = $("#createNewCustomerModal");
    if (!$modal.length) {
        return;
    }

    $modal.off("show.bs.modal.newacct").on("show.bs.modal.newacct", function() {
        var defCreate = $modal.data("default-create-account");
        if (defCreate === 0 || defCreate === "0") {
            $("#create_account").prop("checked", false);
            $("#createNewCustomerModalLabel").text("Add user");
            // Prefer credentials on Users tab
            $("#portal_credentials").prop("checked", true);
        } else {
            $("#create_account").prop("checked", true);
            $("#createNewCustomerModalLabel").text("Create new customer");
            $("#portal_none").prop("checked", true);
        }
        // Reset fields except leaving structure
        $("#userform")[0].reset();
        // re-apply defaults after reset
        if (defCreate === 0 || defCreate === "0") {
            $("#create_account").prop("checked", false);
            $("#portal_credentials").prop("checked", true);
        } else {
            $("#create_account").prop("checked", true);
            $("#portal_none").prop("checked", true);
        }
        new_acct_clear_feedback();
        new_acct_sync_fields();
        $("#createCustomerBtn").prop("disabled", false);
    });

    $("#create_account").off("change.newacct").on("change.newacct", new_acct_update_summary);
    $('input[name="portal_mode"]').off("change.newacct").on("change.newacct", new_acct_sync_fields);

    $("#createCustomerBtn").off("click.newacct").on("click.newacct", function() {
        if (!new_acct_client_validate()) {
            return;
        }

        $("#savingiconnew").show();
        $("#createCustomerBtn").prop("disabled", true);
        var form_data = new_acct_build_payload();

        window.ajax_request({
            type: "POST",
            url: "/users/new",
            payload: JSON.stringify(form_data),
            content_type: "application/json",
            form_parent: "#userform",
            on_response: function(response) {
                $("#savingiconnew").hide();
                $("#createCustomerBtn").prop("disabled", false);
                // ajax_request already marks invalid fields; add modal-level summary
                if (response && response.success === false) {
                    if (response.form_errors) {
                        new_acct_apply_form_errors(response.form_errors);
                    } else if (response.errors) {
                        new_acct_show_alert("danger", (response.errors || []).join(" "));
                    }
                }
            },
            on_success: function(response) {

                if (response.invite) {
                    var msg = response.message || "Invitation created.";
                    if (response.signup_path && !response.email_sent) {
                        msg += " Share this link: " + response.signup_path;
                    }
                    new_acct_show_alert(response.email_sent ? "success" : "warning", msg);
                    if ($("#usermgmt").length || $("#accountmgmt").length) {
                        setTimeout(function() { window.location.reload(); }, 1200);
                        return;
                    }
                    setTimeout(function() { $modal.modal("hide"); }, 1500);
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

                // Users management: go to the new user when we created a login
                if (response.user_id && $("#usermgmt").length) {
                    window.location.href = "/users/" + response.user_id + "/edit";
                    return;
                }

                // Account-only from accounts page
                if (response.account_id && $("#accountmgmt").length) {
                    window.location.href = "/accounts/" + response.account_id + "/edit";
                    return;
                }

                if (response.user_id) {
                    window.location.href = "/users/" + response.user_id + "/edit";
                    return;
                }

                window.location.reload();
            }
        });
    });
}

$(new_acct);
