$(document).ready(function() {
    var row_id;

    if (typeof picklist_data !== "undefined") {
        $("#picklist-select-view").select2({
            data: picklist_data,
            width: "25%"
        });
        $("#picklist-select").select2({
            data: picklist_data,
            width: "25%"
        });
    }

    $(document).on("click", 
        '[data-bs-target="#moveModal"], ' +
        '[data-bs-target="#removeModal"]', 
        function() {
            var tr = $(this).closest("tr");
            row_id = tr.data("row-id");
        }
    );

    $("#picklistview").click(function(event) {
        event.preventDefault();
        let base_url = "/packages/picklists/";
        let picklist_id = $("#picklist-select-view").find(":selected").val();
        window.location.href = base_url + picklist_id;
    });

    // Handle "Save Changes" click in the modal
    $("#moveModal .btn-primary").on("click", function() {
        // Get the selected item's ID from the dropdown
        var selected_item_value = $("#picklist-select").val();

        // Prepare data for POST request
        var post_data = {
            ids: [row_id],
            picklist_id: Number(selected_item_value)
        };

        $.ajax({
            type: "POST",
            url: "/packages/picklists/modify",
            headers: {"X-CSRFToken": window.csrf_token},
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
            headers: {"X-CSRFToken": window.csrf_token},
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
