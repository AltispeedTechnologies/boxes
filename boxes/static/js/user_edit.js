let alias_internal_id = 1;
let email_internal_id = 1;

$(document).ready(function() {
    initial_billable_val = $("#billable").prop("checked");

    $("#aliasesinput").on("mouseenter mouseleave", ".col-md-3", function(event) {
        $(this).find(".fa-trash").toggle(event.type === "mouseenter");
    });

    $("#aliasesinput").on("click", ".fa-trash", function() {
        var input = $(this).siblings("input");
        var current_id = input.attr("data-id");
        
        if (current_id.startsWith("NEW_")) {
            $(this).parent().remove();
        } else {
            $(this).parent().addClass("d-none");
            input.attr("data-id", "REMOVE_" + current_id);
        }
    });

    $("#newaliasbtn").click(function() {
        var input_div = $("<div>", {
            class: "col-md-3 d-flex align-items-center position-relative"
        }).append($("<input>", {
            type: "text",
            class: "form-control",
            "data-id": "NEW_" + alias_internal_id++
        }), $('<i>', {
            class: "fas fa-trash position-absolute end-0 me-4 text-danger",
            css: { display: "none", cursor: "pointer" }
        }));

        $("#aliasesinput").append(input_div);
    });

    $("#savealiasbtn").click(function() {
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

        console.log(aliases);

        $.ajax({
            type: "POST",
            url: "/accounts/aliases/update",
            contentType: "application/json",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(aliases),
            success: function(response) {
                if (response.success) {
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
                } else if (response.errors) {
                    alert("Error: " + response.errors);
                }
            },
            error: function() {
                alert("Error saving data.");
            }
        });
    });

    $("#emailsinput").on("mouseenter mouseleave", ".col-md-3", function(event) {
        $(this).find(".fa-trash").toggle(event.type === "mouseenter");
    });

    $("#emailsinput").on("click", ".fa-trash", function() {
        var input = $(this).siblings("input");
        var current_id = input.attr("data-id");
        
        if (current_id.startsWith("NEW_")) {
            $(this).parent().remove();
        } else {
            $(this).parent().addClass("d-none");
            input.attr("data-id", "REMOVE_" + current_id);
        }
    });

    $("#newemailbtn").click(function() {
        var input_div = $("<div>", {
            class: "col-md-3 d-flex align-items-center position-relative"
        }).append($("<input>", {
            type: "text",
            class: "form-control",
            "data-id": "NEW_" + email_internal_id++
        }), $('<i>', {
            class: "fas fa-trash position-absolute end-0 me-4 text-danger",
            css: { display: "none", cursor: "pointer" }
        }));

        $("#emailsinput").append(input_div);
    });

    $("#saveemailbtn").click(function() {
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

        $.ajax({
            type: "POST",
            url: "/users/emails/update",
            contentType: "application/json",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(emails),
            success: function(response) {
                if (response.success) {
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
                } else if (response.errors) {
                    alert("Error: " + response.errors);
                }
            },
            error: function() {
                alert("Error saving data.");
            }
        });
    });

    $("#savedetailsbtn").click(function() {
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

        $.ajax({
            type: "POST",
            url: "/users/update",
            contentType: "application/json",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(payload),
            success: function(response) {
                $form.find(".is-invalid").removeClass("is-invalid");

                if (response.success) {
                    window.display_error_message();

                    if (billable != initial_billable_val) {
                        let account_id = $("#accountnotes").attr("data-id");
                        let acct_payload = {billable: billable};
                        initial_billable_val = billable;

                        $.ajax({
                            type: "POST",
                            url: "/accounts/" + account_id + "/update",
                            contentType: "application/json",
                            headers: {"X-CSRFToken": window.csrf_token},
                            data: JSON.stringify(acct_payload),
                            success: function(response) {
                                if (response.success) {
                                    window.display_error_message();
                                    $("#savingicondetails").hide();
                                    $("#successicondetails").show();
                                    setTimeout(function() {
                                        $("#successicondetails").fadeOut();
                                    }, 3000);
                                } else if (response.errors) {
                                    window.display_error_message(response.errors);
                                }
                            },
                        });
                    } else {
                        window.display_error_message();
                        $("#savingicondetails").hide();
                        $("#successicondetails").show();
                        setTimeout(function() {
                            $("#successicondetails").fadeOut();
                        }, 3000);
                    }
                } else if (response.errors) {
                    window.display_error_message(response.errors);
                } else if (response.form_errors) {
                    $.each(response.form_errors, function(field, errors) {
                        if (errors.length > 0) {
                            $form.find("#" + field).addClass("is-invalid");
                            $form.find("#" + field).next(".invalid-feedback").text(errors[0]).show();
                        }
                    });
                }
            },
            error: function() {
                alert("Error saving data.");
            }
        });
    });
});
