$(document).ready(function() {
    $("#userform").submit(function(event) {
        event.preventDefault();
        let csrf_token = window.get_cookie("csrftoken");

        var user_id = $(this).data("user-id");
        var form_data = {};
        $(this).serializeArray().forEach(function(item) {
            form_data[item.name] = item.value;
        });
        var $form = $(this);

        var payload = {};
        payload[user_id] = form_data;

        $.ajax({
            type: "POST",
            url: "/users/update",
            contentType: "application/json",
            headers: {"X-CSRFToken": csrf_token},
            data: JSON.stringify(payload),
            success: function(response) {
                $form.find(".is-invalid").removeClass("is-invalid");

                if (response.success) {
                    window.display_error_message();
                    $("#success-icon").show();
                    setTimeout(function() {
                        $("#success-icon").fadeOut();
                    }, 3000);
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
