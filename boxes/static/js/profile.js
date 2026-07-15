/**
 * @file profile.js
 * @description My Profile form submit and email list management.
 * @see docs/api/javascript.md
 */

function init_profile_page() {
    window.email_internal_id = 1;

    $("#emailsinput").off("mouseenter mouseleave", ".col-md-4").on("mouseenter mouseleave", ".col-md-4", function(event) {
        $(this).find(".fa-trash").toggle(event.type === "mouseenter");
    });

    $("#emailsinput").off("click", ".fa-trash").on("click", ".fa-trash", function() {
        var input = $(this).siblings("input");
        var current_id = input.attr("data-id");

        if (current_id.startsWith("NEW_")) {
            $(this).parent().remove();
        } else {
            $(this).parent().addClass("d-none");
            input.attr("data-id", "REMOVE_" + current_id);
        }
    });

    $("#newemailbtn").off("click").on("click", function() {
        $("#noemailsmsg").remove();
        var input_div = $("<div>", {
            class: "col-md-4 d-flex align-items-center position-relative mb-2"
        }).append($("<input>", {
            type: "email",
            class: "form-control",
            "data-id": "NEW_" + window.email_internal_id++
        }), $("<i>", {
            class: "fas fa-trash position-absolute end-0 me-4 text-danger",
            css: { display: "none", cursor: "pointer" }
        }));

        $("#emailsinput").append(input_div);
    });

    $("#saveemailbtn").off("click").on("click", function() {
        $("#savingiconemails").show();
        var emails = {};

        $("#emailsinput div input").each(function() {
            var input = $(this);
            emails[input.attr("data-id")] = input.val();
        });

        if ($.isEmptyObject(emails)) {
            $("#savingiconemails").hide();
            return;
        }

        window.ajax_request({
            type: "POST",
            url: "/profile/emails/update",
            payload: JSON.stringify({ emails: emails }),
            content_type: "application/json",
            on_success: function(response) {
                $.each(response.emails, function(old_id, new_id) {
                    if (old_id.startsWith("NEW_")) {
                        $('input[data-id="' + old_id + '"]').attr("data-id", new_id);
                    } else if (old_id.startsWith("REMOVE_")) {
                        $('input[data-id="' + old_id + '"]').closest("div").remove();
                    }
                });
                $("#savingiconemails").hide();
                $("#successiconemails").show();
                setTimeout(function() { $("#successiconemails").fadeOut(); }, 3000);
            }
        });
    });

    $("#savedetailsbtn").off("click").on("click", function() {
        $("#savingicondetails").show();
        var $form = $("#profileform");

        var form_data = {};
        $form.serializeArray().forEach(function(item) {
            form_data[item.name] = item.value;
        });

        window.ajax_request({
            type: "POST",
            url: "/profile/update",
            payload: JSON.stringify(form_data),
            content_type: "application/json",
            form_parent: $form,
            on_success: function(response) {
                $("#savingicondetails").hide();
                $("#successicondetails").show();
                // Clear password fields after a successful change
                $("#new_password1, #new_password2").val("");
                setTimeout(function() {
                    $("#successicondetails").fadeOut();
                }, 3000);
            },
            on_response: function(response) {
                $form.find(".is-invalid").removeClass("is-invalid");
                $("#savingicondetails").hide();
            }
        });
    });
}

$(init_profile_page);
