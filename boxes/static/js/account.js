/**
 * @file account.js
 * @description Staff account detail page interactions (comments, membership, web accounts, fee waiver).
 * @see docs/api/javascript.md
 */

function init_account_page() {
    $("#accountnotes").off("input").on("input", window.debounce(function() {
        $("#savingnotes").removeClass("d-none");
        var account_id = $(this).attr("data-id");

        var new_comments = $(this).val();
        var payload = JSON.stringify({"comments": new_comments});

        window.ajax_request({
            type: "POST",
            url: "/accounts/" + account_id + "/update",
            payload: payload,
            content_type: "application/json",
            on_success: function(response) {
                $("#savingnotes").addClass("d-none");
                $("#donesavingnotes").show();
                $("#donesavingnotes").fadeOut(2000);
            }
        });
    }, 500));

    if ($("input#billable").length === 1) {
        $("input#billable").off("change").on("change", function() {
            var $input = $(this);
            $input.prop("disabled", true);
            $("#savingiconbillable").show();

            var acct_payload = {billable: $(this).prop("checked")};
            var account_id = $(this).attr("data-id");

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

    var $memberships = $("#account-memberships");
    if ($memberships.length === 1) {
        var membership_account_id = $memberships.data("account-id");

        $("#link-member-btn").off("click").on("click", function() {
            var user_id = $("#link-member-user-id").val();
            var username = ($("#link-member-username").val() || "").trim();
            var role = $("#link-member-role").val() || "member";
            if (!user_id && !username) {
                window.display_error_message(["Enter a user id or username."]);
                return;
            }
            var payload = {role: role};
            if (user_id) {
                payload.user_id = user_id;
            }
            if (username) {
                payload.username = username;
            }
            window.ajax_request({
                type: "POST",
                url: "/accounts/" + membership_account_id + "/members/link",
                payload: JSON.stringify(payload),
                content_type: "application/json",
                on_success: function() {
                    window.location.reload();
                }
            });
        });

        $memberships.off("click", ".disassociate-member").on("click", ".disassociate-member", function() {
            var user_id = $(this).data("user-id");
            if (!window.confirm("Disassociate this user from the account?")) {
                return;
            }
            window.ajax_request({
                type: "POST",
                url: "/accounts/" + membership_account_id + "/members/disassociate",
                payload: JSON.stringify({user_id: user_id}),
                content_type: "application/json",
                on_success: function() {
                    window.location.reload();
                }
            });
        });

        $("#create-web-account-btn").off("click").on("click", function() {
            var $form = $("#create-web-account-form");
            $form.find(".is-invalid").removeClass("is-invalid");
            var payload = {
                username: ($("#web-username").val() || "").trim(),
                password: $("#web-password").val() || "",
                password2: $("#web-password2").val() || "",
                role: $("#web-role").val() || "owner",
                first_name: ($("#web-first-name").val() || "").trim(),
                last_name: ($("#web-last-name").val() || "").trim(),
                email: ($("#web-email").val() || "").trim()
            };
            if (!payload.username || !payload.password) {
                window.display_error_message(["Username and password are required."]);
                return;
            }
            if (payload.password !== payload.password2) {
                window.display_error_message(["Passwords do not match."]);
                return;
            }
            window.ajax_request({
                type: "POST",
                url: "/accounts/" + membership_account_id + "/members/create",
                payload: JSON.stringify(payload),
                content_type: "application/json",
                on_success: function() {
                    window.location.reload();
                }
            });
        });


        $memberships.off("change", ".member-role-select").on("change", ".member-role-select", function() {
            var user_id = $(this).data("user-id");
            var role = $(this).val();
            window.ajax_request({
                type: "POST",
                url: "/accounts/" + membership_account_id + "/members/role",
                payload: JSON.stringify({user_id: user_id, role: role}),
                content_type: "application/json",
                on_success: function() {
                    if (window.BoxesSetupStatus) {
                        window.BoxesSetupStatus.refresh();
                    }
                }
            });
        });

        $("#account-invite-btn").off("click").on("click", function() {
            var $result = $("#account-invite-result");
            $result.text("Sending…");
            window.ajax_request({
                type: "POST",
                url: "/users/invite",
                payload: JSON.stringify({
                    email: ($("#account-invite-email").val() || "").trim(),
                    first_name: ($("#account-invite-first").val() || "").trim(),
                    last_name: ($("#account-invite-last").val() || "").trim(),
                    role: $("#account-invite-role").val() || "owner",
                    account_id: membership_account_id,
                    create_account: false
                }),
                content_type: "application/json",
                on_success: function(response) {
                    var msg = response.email_sent
                        ? "Invitation emailed to " + response.email
                        : "Invite created. Share this link: " + (response.signup_path || "");
                    if (response.last_error) {
                        msg += " (" + response.last_error + ")";
                    }
                    $result.text(msg);
                }
            });
        });

    }
}

$(init_account_page);
