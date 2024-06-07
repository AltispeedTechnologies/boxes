function init_user_edit_page() {
    window.alias_internal_id = 1;
    window.email_internal_id = 1;

    let initial_billable_val = $("#billable").prop("checked");

    $("#aliasesinput").off("mouseenter mouseleave", ".col-md-3").on("mouseenter mouseleave", ".col-md-3", function(event) {
        $(this).find(".fa-trash").toggle(event.type === "mouseenter");
    });

    $("#aliasesinput").off("click", ".fa-trash").on("click", ".fa-trash", function() {
        var input = $(this).siblings("input");
        var current_id = input.attr("data-id");
        
        if (current_id.startsWith("NEW_")) {
            $(this).parent().remove();
        } else {
            $(this).parent().addClass("d-none");
            input.attr("data-id", "REMOVE_" + current_id);
        }
    });

    $("#newaliasbtn").off("click").on("click", function() {
        var input_div = $("<div>", {
            class: "col-md-3 d-flex align-items-center position-relative"
        }).append($("<input>", {
            type: "text",
            class: "form-control",
            "data-id": "NEW_" + window.alias_internal_id++
        }), $('<i>', {
            class: "fas fa-trash position-absolute end-0 me-4 text-danger",
            css: { display: "none", cursor: "pointer" }
        }));

        $("#aliasesinput").append(input_div);
    });

    $("#savealiasbtn").off("click").on("click", function() {
        $("#savingiconaliases").show();
        var aliases = {};
        var account_id = $("#aliasesinput").data("account-id");
        aliases[account_id] = {};

        $("#aliasesinput div input").each(function() {
            var input = $(this);
            aliases[account_id][input.attr("data-id")] = input.val();
        });

        // Do nothing if there are no aliases
        if ($.isEmptyObject(aliases[account_id])) {
            $("#savingiconaliases").hide();
            return;
        }

        window.ajax_request({
            type: "POST",
            url: "/accounts/aliases/update",
            payload: JSON.stringify(aliases),
            content_type: "application/json",
            on_success: function(response) {
                $.each(response.aliases, function(old_id, new_id) {
                    if (old_id.startsWith("NEW_")) {
                        $('input[data-id="' + old_id + '"]').attr("data-id", new_id);
                    } else if (old_id.startsWith("REMOVE_")) {
                        $('input[data-id="' + old_id + '"]').closest("div").remove();
                    }
                });
                $("#savingiconaliases").hide();
                $("#successiconaliases").show();
                setTimeout(function() { $("#successiconaliases").fadeOut(); }, 3000);
            }
        });
    });

    $("#emailsinput").off("mouseenter mouseleave", ".col-md-3").on("mouseenter mouseleave", ".col-md-3", function(event) {
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
        var input_div = $("<div>", {
            class: "col-md-3 d-flex align-items-center position-relative"
        }).append($("<input>", {
            type: "text",
            class: "form-control",
            "data-id": "NEW_" + window.email_internal_id++
        }), $('<i>', {
            class: "fas fa-trash position-absolute end-0 me-4 text-danger",
            css: { display: "none", cursor: "pointer" }
        }));

        $("#emailsinput").append(input_div);
    });

    $("#saveemailbtn").off("click").on("click", function() {
        $("#savingiconemails").show();
        var emails = {};
        var account_id = $("#emailsinput").data("user-id");
        emails[account_id] = {};

        $("#emailsinput div input").each(function() {
            var input = $(this);
            emails[account_id][input.attr("data-id")] = input.val();
        });

        // Do nothing if there are no emails
        if ($.isEmptyObject(emails[account_id])) {
            $("#savingiconemails").hide();
            return;
        }

        window.ajax_request({
            type: "POST",
            url: "/users/emails/update",
            payload: JSON.stringify(emails),
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
        var $form = $("#userform");

        var user_id = $form.data("user-id");
        var form_data = {};
        $form.serializeArray().forEach(function(item) {
            form_data[item.name] = item.value;
        });

        let billable = $("#billable").prop("checked");

        var payload = {};
        payload[user_id] = form_data;

        window.ajax_request({
            type: "POST",
            url: "/users/update",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function(response) {
                if (billable != initial_billable_val) {
                    let account_id = $("#accountnotes").attr("data-id");
                    let acct_payload = {billable: billable};
                    initial_billable_val = billable;

                    window.ajax_request({
                        type: "POST",
                        url: "/accounts/" + account_id + "/update",
                        payload: JSON.stringify(acct_payload),
                        content_type: "application/json",
                        on_success: function(response) {
                            window.display_error_message();
                            $("#savingicondetails").hide();
                            $("#successicondetails").show();
                            setTimeout(function() {
                                $("#successicondetails").fadeOut();
                            }, 3000);
                        }
                    });
                } else {
                    $("#savingicondetails").hide();
                    $("#successicondetails").show();
                    setTimeout(function() {
                        $("#successicondetails").fadeOut();
                    }, 3000);
                }
            },
            on_response: function(response) {
                $form.find(".is-invalid").removeClass("is-invalid");
            }
        });
    });
}

if ($("#accountedit").length !== 0) {
    init_user_edit_page();
}
