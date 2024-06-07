$(document).ready(function() {
    $("#content").summernote({
        airMode: false,
        width: "100%",
        height: 480,
        toolbar: [
            ["style", ["style"]],
            ["font", ["bold", "italic", "underline", "clear"]],
            ["color", ["color"]],
            ["fontname", ["fontname"]],
            ["para", ["ul", "ol", "paragraph"]],
            ["insert", ["link", "custom_block"]],
            ["view", ["fullscreen", "help"]],
        ],
        popover: {
            air: [
                ["color", ["color"]],
                ["font", ["bold", "underline", "clear"]]
            ]
        },
        disableDragAndDrop: true,
        lang: "en-US",
        dialogsInBody: true,
        dialogsFade: true,
    });
});

function init_email_template_mgmt_page() {
    $("#template-selector").select2();
    window.select2properheight("#template-selector");

    $("#template-selector").change(function() {
        var id = $(this).val();

        $.ajax({
            url: "/mgmt/email/templates/fetch",
            type: "GET",
            data: {"id": id},
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            success: function(data) {
                $("#content").summernote("code", data.content);
                $("#email_subject").val(data.subject);
            }
        });
    });

    $("#save-btn").off("click").on("click", function() {
        $("#savingicon").show();
        var template_id = $("#template-selector").val();
        var content = $("#content").summernote("code");
        var subject = $("#email_subject").val();

        $.ajax({
            url: "/mgmt/email/templates/update",
            type: "POST",
            data: {
                "id": template_id,
                "content": content,
                "subject": subject
            },
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            success: function(response) {
                window.display_error_message();
                if (response.success) {
                    $("#savingicon").hide();
                    $("#successicon").show();
                    $("#successicon").fadeOut(2000);
                } else {
                    window.display_error_message(response.errors);
                }
            }
        });
    });

    $("#addTemplateForm").off("submit").on("submit", function(event) {
        event.preventDefault();
        var template_name = $("#templateName").val();

        $.ajax({
            type: "POST",
            url: "/mgmt/email/templates/add",
            data: {name: template_name},
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            success: function(response) {
                window.display_error_message();

                if (response.success) {
                    var new_option = new Option(template_name, response.id, true, true);
                    $("#template-selector").append(new_option).trigger("change");
                    $("#templateName").val("");
                    $("#email_subject").val("");
                    $("#addTemplateModal").modal("hide");
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(response) {
                window.display_error_message(response.errors);
            }
        });
    });
}

if ($("div#emailtemplatemgmt").length !== 0) {
    init_email_template_mgmt_page();
}
