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

    $("#template-selector").select2();
    $("#template-selector").on("change", function() {
        var id = $(this).val();
        $.ajax({
            url: "/mgmt/email/templates/fetch",
            type: "GET",
            data: {"id": id},
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", window.csrf_token);
            },
            success: function(data) {
                $("#content").summernote("code", data.content);
            }
        });
    });

    $("#save-btn").click(function() {
        $("#savingicon").show();
        var template_id = $("#template-selector").val();
        var content = $("#content").summernote("code");

        $.ajax({
            url: "/mgmt/email/templates/update",
            type: "POST",
            data: {
                "id": template_id,
                "content": content,
            },
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", window.csrf_token);
            },
            success: function(response) {
                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
            }
        });
    });
});
