function new_acct() {
    $("#createNewCustomerModal .btn-primary").off("click").on("click", function() {
        $("#savingiconnew").show();
        var $form = $("#userform");

        var form_data = {};
        $form.serializeArray().forEach(function(item) {
            form_data[item.name] = item.value;
        });

        window.ajax_request({
            type: "POST",
            url: "/users/new",
            payload: JSON.stringify(form_data),
            content_type: "application/json",
            on_response: function() {
                $form.find(".is-invalid").removeClass("is-invalid");
                $("#savingiconnew").hide();
            },
            on_success: function(response) {
                var option = new Option(response.account_name, response.account_id, true, true);
                $("#id_account_id").append(option);
                $("#id_account_id").val(response.account_id).trigger("change");
                $("#createNewCustomerModal").modal("hide");
            }
        });
    });
}

if ($("#createNewCustomerModal").length !== 0) {
    new_acct();
}
