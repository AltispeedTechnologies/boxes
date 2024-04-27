$(document).ready(function() {
    var selected_packages = selected_packages || new Set();
    if (selected_packages.size > 0) { update_pagination_links(); }

    let last_checked = null;
    var row_id;
    let csrfToken = window.get_cookie("csrftoken");

    if (typeof picklist_data !== "undefined") {
        $("#picklist-select").select2({
            data: picklist_data
        });

        $("#picklist-select").data("select2").$container.addClass("my-2 float-end");
    }

    // Directly attaching the event listener to ensure it's registered immediately
    $(document).on("click", ".package-checkbox", function(e) {
        let package_id = this.id.split("-")[1];
        
        // Check for the first click with a more reliable condition
        if (!last_checked) {
            last_checked = this;
            update_package_selection(this.checked, package_id);
            return;
        }

        if (e.shiftKey && last_checked) {
            handle_shift_select(this, last_checked);
        } else {
            update_package_selection(this.checked, package_id);
        }

        last_checked = this;
    });

    function update_pagination_links() {
        // Convert the Set to a comma-separated string
        let selected_ids_str = Array.from(selected_packages).join(",");

        // Update each pagination link with the selected_ids parameter
        document.querySelectorAll(".pagination .page-link").forEach(link => {
            let url = new URL(link.href, window.location.origin);
            url.searchParams.set("selected_ids", selected_ids_str);
            link.href = url.toString();
        });
    }

    function handle_shift_select(current, last) {
        let start = $(".package-checkbox").index(current);
        let end = $(".package-checkbox").index(last);
        $(".package-checkbox").slice(Math.min(start, end), Math.max(start, end) + 1).each(function() {
            this.checked = last.checked;
            update_package_selection(this.checked, this.id.split("-")[1]);
        });
    }

    function update_package_selection(is_checked, package_id) {
        if (is_checked) {
            selected_packages.add(package_id);
        } else {
            selected_packages.delete(package_id);
        }

        update_pagination_links();
    }

    $("#picklistview").click(function(event) {
        event.preventDefault();
        let base_url = "/packages/picklists/";
        let picklist_id = $("#picklist-select").find(":selected").val();
        window.location.href = base_url + picklist_id;
    });

    $("#picklistbtn").click(function(event) {
        event.preventDefault();
        let packages_array = Array.from(selected_packages);
        let picklist_id = $("#picklist-select").find(":selected").val();
        let packages_payload = {
            "ids": packages_array,
            "picklist_id": picklist_id
        };
        
        $.ajax({
            type: "POST",
            url: "/packages/picklists/add",
            headers: {"X-CSRFToken": csrfToken},
            data: JSON.stringify(packages_payload),
            contentType: "application/json", // Specify the content type
            success: function(response) {
                if (response.success) {
                    window.location.href = response.redirect_url;
                } else {
                    console.error("Addition to picklist failed:", response.errors.join("; "));
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
            headers: {"X-CSRFToken": csrfToken},
            data: JSON.stringify(post_data),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    console.error("Move to picklist failed:", response.errors.join("; "));
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
            headers: {"X-CSRFToken": csrfToken},
            data: JSON.stringify(post_data),
            contentType: "application/json",
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    console.error("Removal from picklist failed:", response.errors.join("; "));
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });
});
