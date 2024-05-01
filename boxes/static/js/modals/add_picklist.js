var row_id;

$(document).ready(function() {
    let csrf_token = window.get_cookie("csrftoken");

    $.ajax({
        type: "GET",
        url: "/picklists/query",
        headers: {
            "X-CSRFToken": csrf_token
        },
        success: function(response) {
            console.log(response.results);
            $("#picklist-select").select2({
                data: response.results,
                dropdownParent: "#addPicklistModal",
                width: "100%"
            });
        },
        error: function(xhr, status, error) {
            window.display_error_message(error);
        }
    });

    $("[data-bs-target=\"#addPicklistModal\"]").on("click", function() {
        var tr = $(this).closest("tr");
        row_id = tr.data("row-id");
    });

    $("#addPicklistModal .btn-primary").on("click", function() {
        event.preventDefault();
        let picklist_id = $("#picklist-select").find(":selected").val();
        let packages_payload = {
            "ids": [row_id],
            "picklist_id": picklist_id
        };
        
        $.ajax({
            type: "POST",
            url: "/packages/picklists/add",
            headers: {"X-CSRFToken": csrf_token},
            data: JSON.stringify(packages_payload),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });
});
