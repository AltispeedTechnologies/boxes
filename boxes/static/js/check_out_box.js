function verify_package() {
    window.display_error_message();
    $("#savingicon").show();
    let picklist_id = $("#tracking_code").attr("data-picklist-id");
    let form_data = {tracking_code: $("#tracking_code").val()};

    if (picklist_id !== "") {
        form_data["picklist_id"] = picklist_id;
    }

    if (window.queued_packages === undefined) {
        window.queued_packages = new Set();
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
                window.queued_packages.add(package_id);
                $("#successicon").show();
                $("#successicon").fadeOut(1000);
                $(document).trigger("checkoutPackageValid", [response.package]);
            }
        },
        on_response: function(response) {
            $("#tracking_code").val("");
            $("#savingicon").hide();
        }
    });
}

function setup_checkout_box() {
    $("#tracking_code").off("keydown").on("keydown", function(event) {
        if (event.keyCode === 13) {  // Enter key
            event.preventDefault();
            verify_package();
        }
    });
}

if ($("input#tracking_code").length !== 0) {
    setup_checkout_box();
}
