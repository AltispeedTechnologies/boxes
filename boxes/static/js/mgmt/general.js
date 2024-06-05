$(document).ready(function() {
    $("#clear-file").on("click", function() {
        $("#image").val("");
        $(this).prop("disabled", true);
    });

    $("#image").on("change", function() {
        var selected = $(this).val() !== "";
        $("#clear-file").prop("disabled", !selected);
    });

    $("#saveconfig").on("click", function() {
        // Create FormData object to hold the file data
        var form_data = new FormData();
        // Get the file from the file input
        var image_file = $("#image")[0].files[0];

        // Check if there is a file selected
        if (image_file) {
            // Append the file to the form data
            form_data.append("image", image_file);

            // Display the saving icon
            $("#savingicon").show();

            $.ajax({
                url: "/mgmt/general/update",
                type: "POST",
                data: form_data,
                contentType: false,
                processData: false,
                headers: {
                    "X-CSRFToken": window.csrf_token
                },
                success: function() {
                    $("#savingicon").hide();
                    $("#successicon").show();
                    $("#successicon").fadeOut(2000);
                }
            });
        } else {
            alert("Please select an image file to upload.");
        }
    });
});
