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

        window.ajax_request({
            type: "GET",
            url: "/mgmt/email/templates/fetch",
            payload: {"id": id},
            on_success: function(response) {
                $("#content").summernote("code", response.content);
                $("#email_subject").val(response.subject);
            }
        });
    });

    $("#save-btn").off("click").on("click", function() {
        $("#savingicon").show();
        var template_id = $("#template-selector").val();
        var content = $("#content").summernote("code");
        var subject = $("#email_subject").val();
        var payload = {
            "id": template_id,
            "content": content,
            "subject": subject
        };

        window.ajax_request({
            type: "POST",
            url: "/mgmt/email/templates/update",
            payload: payload,
            on_success: function() {
                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
            }
        });
    });

    $("#addTemplateForm").off("submit").on("submit", function(event) {
        event.preventDefault();
        var template_name = $("#templateName").val();

        window.ajax_request({
            type: "POST",
            url: "/mgmt/email/templates/add",
            payload: {name: template_name},
            on_success: function(response) {
                var new_option = new Option(template_name, response.id, true, true);
                $("#template-selector").append(new_option).trigger("change");
                $("#templateName").val("");
                $("#email_subject").val("");
                $("#addTemplateModal").modal("hide");
            }
        });
    });
}

window.manage_init_func("div#emailtemplatemgmt", "email_template", init_email_template_mgmt_page);
