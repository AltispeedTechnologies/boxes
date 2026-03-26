$(document).ready(function() {
    const make_btn = (name, text) => ({
        name: name,
        text: text, 
        tooltip: "Insert " + text,
        exec: (editor) => {
            editor.selection.insertHTML(`<span contenteditable="false" style="user-select: none;" class="custom-block bg-light mx-1 p-2">${text}</span>`);
        }
    });

    const editor = Jodit.make("#content-editor", {
        height: 400,
        toolbarAdaptive: false,
        buttons: [
            "bold", "italic", "underline", "strikethrough", "|",
            "link", "|",
            "first_name", "last_name", "full_name", "tracking_code", "carrier", "comment", "|",
            "eraser"
        ],
        controls: {
            first_name: make_btn("first_name", "First Name"),
            last_name: make_btn("last_name", "Last Name"),
            full_name: make_btn("full_name", "Full Name"),
            tracking_code: make_btn("tracking_code", "Tracking Code"),
            carrier: make_btn("carrier", "Carrier"),
            comment: make_btn("comment", "Comment")
        }
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
                $(".jodit-wysiwyg")[0].innerHTML = response.content;
                $("#email_subject").val(response.subject);
            }
        });
    });

    $("#save-btn").off("click").on("click", function() {
        $("#savingicon").show();
        var template_id = $("#template-selector").val();
        var content = $("#content-editor").val();
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

$(init_email_template_mgmt_page);
