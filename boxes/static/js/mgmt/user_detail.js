/**
 * @file mgmt/user_detail.js
 * @description Staff user detail: access, password, account links, invites.
 */

function init_user_detail_page() {
    var $root = $("#userdetail");
    if (!$root.length) {
        return;
    }
    var userId = $root.data("user-id");

    // Profile save (reuses /users/update shape)
    $("#savedetailsbtn").off("click.userdetail").on("click.userdetail", function() {
        $("#savingicondetails").show();
        var payload = {};
        payload[userId] = {};
        $("#userdetailsform").serializeArray().forEach(function(item) {
            payload[userId][item.name] = item.value;
        });
        window.ajax_request({
            type: "POST",
            url: "/users/update",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_response: function() {
                $("#savingicondetails").hide();
            },
            on_success: function() {
                $("#successicondetails").show();
                setTimeout(function() { $("#successicondetails").fadeOut(); }, 3000);
            }
        });
    });

    // Emails: reuse selectors from user_edit.js patterns if present; otherwise inline
    if (typeof window.email_internal_id === "undefined") {
        window.email_internal_id = 1;
    }
    $("#emailsinput").off("mouseenter mouseleave", ".col-md-3")
        .on("mouseenter mouseleave", ".col-md-3", function(event) {
            $(this).find(".fa-trash").toggle(event.type === "mouseenter");
        });
    $("#emailsinput").off("click", ".fa-trash").on("click", ".fa-trash", function() {
        var input = $(this).siblings("input");
        var current_id = input.attr("data-id");
        if (String(current_id).startsWith("NEW_")) {
            $(this).parent().remove();
        } else {
            $(this).parent().addClass("d-none");
            input.attr("data-id", "REMOVE_" + current_id);
        }
    });
    $("#newemailbtn").off("click.userdetail").on("click.userdetail", function() {
        var input_div = $("<div>", {
            class: "col-md-3 d-flex align-items-center position-relative mb-2"
        }).append($("<input>", {
            type: "text",
            class: "form-control",
            "data-id": "NEW_" + window.email_internal_id++
        }), $("<i>", {
            class: "fas fa-trash position-absolute end-0 me-4 text-danger",
            css: { display: "none", cursor: "pointer" }
        }));
        $("#emailsinput").append(input_div);
    });
    $("#saveemailbtn").off("click.userdetail").on("click.userdetail", function() {
        $("#savingiconemails").show();
        var emails = {};
        emails[userId] = {};
        $("#emailsinput div input").each(function() {
            var input = $(this);
            emails[userId][input.attr("data-id")] = input.val();
        });
        window.ajax_request({
            type: "POST",
            url: "/users/emails/update",
            payload: JSON.stringify(emails),
            content_type: "application/json",
            on_success: function(response) {
                $.each(response.emails || {}, function(old_id, new_id) {
                    if (String(old_id).startsWith("NEW_")) {
                        $('input[data-id="' + old_id + '"]').attr("data-id", new_id);
                    } else if (String(old_id).startsWith("REMOVE_")) {
                        $('input[data-id="' + old_id + '"]').closest("div").remove();
                    }
                });
                $("#savingiconemails").hide();
                $("#successiconemails").show();
                setTimeout(function() { $("#successiconemails").fadeOut(); }, 3000);
            }
        });
    });

    $("#save-access-btn").off("click").on("click", function() {
        var groups = [];
        $(".user-group-check:checked").each(function() {
            groups.push($(this).val());
        });
        window.ajax_request({
            type: "POST",
            url: "/users/" + userId + "/status",
            payload: JSON.stringify({
                is_active: $("#user-is-active").is(":checked"),
                groups: groups
            }),
            content_type: "application/json",
            on_success: function() {
                window.location.reload();
            }
        });
    });

    $("#set-password-btn").off("click").on("click", function() {
        $("#set-password").removeClass("is-invalid");
        window.ajax_request({
            type: "POST",
            url: "/users/" + userId + "/status",
            payload: JSON.stringify({
                password: $("#set-password").val(),
                password2: $("#set-password2").val()
            }),
            content_type: "application/json",
            on_success: function() {
                $("#set-password").val("");
                $("#set-password2").val("");
                window.alert("Password updated.");
            }
        });
    });

    $root.off("change", ".user-account-role-select").on("change", ".user-account-role-select", function() {
        var accountId = $(this).data("account-id");
        var role = $(this).val();
        window.ajax_request({
            type: "POST",
            url: "/users/" + userId + "/accounts/role",
            payload: JSON.stringify({ account_id: accountId, role: role }),
            content_type: "application/json",
            on_success: function() {}
        });
    });

    $("#link-account-btn").off("click").on("click", function() {
        window.ajax_request({
            type: "POST",
            url: "/users/" + userId + "/accounts/link",
            payload: JSON.stringify({
                account_id: $("#link-account-id").val(),
                role: $("#link-account-role").val()
            }),
            content_type: "application/json",
            on_success: function() {
                window.location.reload();
            }
        });
    });

    $(".unlink-account").off("click").on("click", function() {
        var accountId = $(this).data("account-id");
        if (!window.confirm("Unlink this billing account from the user?")) {
            return;
        }
        window.ajax_request({
            type: "POST",
            url: "/users/" + userId + "/accounts/unlink",
            payload: JSON.stringify({ account_id: accountId }),
            content_type: "application/json",
            on_success: function() {
                window.location.reload();
            }
        });
    });
    });
}

$(init_user_detail_page);
