function init_email_mgmt_page() {
    $("#add-day-template").off("click").on("click", function() {
        var new_entry = $(".day-template.d-none").clone().removeClass("d-none");
        new_entry.find("input").val("");
        new_entry.find("select").prop("selectedIndex", 0);
        new_entry.find(".remove-day-template").click(function() {
            $(this).closest(".day-template").remove();
        });
        $("#days-templates").append(new_entry);
    });

    $(".remove-day-template").off("click").on("click", function() {
        $(this).closest(".day-template").remove();
    });

    $("#saveconfig").off("click").on("click", function() {
        $("#savingicon").show();

        var form_data = {
            sender_name: $("#sender-name").val(),
            sender_email: $("#sender-email").val(),
            check_in_template: $("#check-in-template").val(),
            notification_rules: []
        };

        $(".day-template:not(.d-none)").each(function() {
            var days = $(this).find("input[type=\"number\"]").val();
            var template_id = $(this).find("select").val();
            if (days && template_id) {
                form_data.notification_rules.push({ days: days, template_id: template_id });
            }
        });

        $.ajax({
            url: "/mgmt/email/update",
            type: "POST",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            data: JSON.stringify(form_data),
            success: function() {
                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
            }
        });
    });
}

if ($("div#emailmgmt").length !== 0) {
    init_email_mgmt_page();
}
