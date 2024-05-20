$(document).ready(function() {
    $("#createNewCustomerModal .btn-primary").on("click", function() {
        $("#savingiconnew").show();
        var $form = $("#userform");

        var form_data = {};
        $form.serializeArray().forEach(function(item) {
            form_data[item.name] = item.value;
        });

        $.ajax({
            type: "POST",
            url: "/users/new",
            contentType: "application/json",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(form_data),
            success: function(response) {
                $form.find(".is-invalid").removeClass("is-invalid");
                $("#savingiconnew").hide();

                if (response.success) {
                    var option = new Option(response.account_name, response.account_id, true, true);
                    $("#id_account_id").append(option);
                    $("#id_account_id").val(response.account_id).trigger("change");
                    $("#createNewCustomerModal").modal("hide");
                } else if (response.form_errors) {
                    $.each(response.form_errors, function(field, errors) {
                        if (errors.length > 0) {
                            $form.find("#" + field).addClass("is-invalid");
                            $form.find("#" + field).next(".invalid-feedback").text(errors[0]).show();
                        }
                    });
                }
            }
        });
    });
});
