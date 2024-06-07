function init_general_mgmt_page() {
    $("#clear-file").off("click").on("click", function() {
        $("#image").val("");
        $(this).prop("disabled", true);
    });

    $("#image").off("change").on("change", function() {
        var selected = $(this).val() !== "";
        $("#clear-file").prop("disabled", !selected);
    });

    $("#saveconfig").off("click").on("click", function() {
        // Display the saving icon
        $("#savingicon").show();

        // Create FormData object to hold the file data
        var form_data = new FormData();
        // Get the file from the file input
        var image_file = $("#image")[0].files[0];
        // Append the file to the form data if it exists
        if (image_file) {
            form_data.append("image", image_file);
        }

        // Include the form fields
        var payload = {
            name: $("#business-name").val(),
            address1: $("#address-1").val(),
            address2: $("#address-2").val(),
            website: $("#website").val(),
            email: $("#email").val(),
            phone_number: $("#phone_number").val()
        };
        form_data.append("payload", JSON.stringify(payload));

        window.ajax_request({
            type: "POST",
            url: "/mgmt/general/update",
            payload: form_data,
            content_type: false,
            process_data: false,
            on_success: function() {
                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
            }
        });
    });
}

if ($("div#generalmgmt").length !== 0) {
    init_general_mgmt_page();
}
