function verify_package() {
    window.display_error_message();
    $("#savingicon").show();
    let picklist_id = $("#tracking_code").attr("data-picklist-id");
    let form_data = {tracking_code: $("#tracking_code").val()};

    if (picklist_id !== "") {
        form_data["picklist_id"] = picklist_id;
    }

    window.ajax_request({
        type: "POST",
        url: "/packages/checkout/verify",
        payload: JSON.stringify(form_data),
        content_type: "application/json",
        on_success: function(response) {
            let package_id = response.package.id;

            if (window.queued_packages.has(package_id)) {
                window.display_error_message(["Parcel already in list"]);
            } else {
                display_packages(response.package);
                window.queued_packages.add(package_id);
                $("#successicon").show();
                $("#successicon").fadeOut(1000);
            }
        },
        on_response: function() {
            $("#tracking_code").val("");
            $("#savingicon").hide();
        }
    });
}
