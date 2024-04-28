$(document).ready(function() {
    var row_id;
    let csrf_token = window.get_cookie("csrftoken");

    if (typeof picklist_data !== "undefined") {
        $("#picklist-select").select2({
            data: picklist_data
        });

        $("#picklist-select").data("select2").$container.addClass("my-2 float-end");
    }

    $(document).on("selectedPackagesUpdated", function(event) {
        $("#picklistbtn").prop("disabled", (window.selected_packages.size == 0));
    });

    $("#picklistview").click(function(event) {
        event.preventDefault();
        let base_url = "/packages/picklists/";
        let picklist_id = $("#picklist-select").find(":selected").val();
        window.location.href = base_url + picklist_id;
    });

    $("#picklistbtn").click(function(event) {
        event.preventDefault();
        let packages_array = Array.from(window.selected_packages);
        let picklist_id = $("#picklist-select").find(":selected").val();
        let packages_payload = {
            "ids": packages_array,
            "picklist_id": picklist_id
        };
        
        $.ajax({
            type: "POST",
            url: "/packages/picklists/add",
            headers: {"X-CSRFToken": csrf_token},
            data: JSON.stringify(packages_payload),
            contentType: "application/json", // Specify the content type
            success: function(response) {
                if (response.success) {
                    window.location.href = response.redirect_url;
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    $("[data-bs-target=\"#moveModal\"]").on("click", function() {
        row_id = $(this).data("row-id"); // Capture the row ID from button
    });

    // Handle "Save Changes" click in the modal
    $("#moveModal .btn-primary").on("click", function() {
        // Get the selected item's ID from the dropdown
        var selected_item_value = $("#picklist-select").val();

        // Prepare data for POST request
        var post_data = {
            row_id: row_id,
            item_id: Number(selected_item_value)
        };

        $.ajax({
            type: "POST",
            url: "/packages/picklists/move",
            headers: {"X-CSRFToken": csrf_token},
            data: JSON.stringify(post_data),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    console.error("Move to picklist failed:", response.errors.join("; "));
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });

    $("[data-bs-target=\"#removeModal\"]").on("click", function() {
        row_id = $(this).data("row-id"); // Capture the row ID from button
    });

    // Handle "Save Changes" click in the modal
    $("#removeModal .btn-primary").on("click", function() {
        const id_array = [row_id];

        // Prepare data for POST request
        var post_data = {
            ids: id_array
        };

        $.ajax({
            type: "POST",
            url: "/packages/picklists/remove",
            headers: {"X-CSRFToken": csrf_token},
            data: JSON.stringify(post_data),
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
