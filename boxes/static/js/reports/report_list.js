function init_report_list() {
    // Store the row ID for deletion
    let current_id = 0;

    // Set the ID to be removed
    $(document).on("click", "[data-bs-target=\"#removeReportModal\"]", function() {
        current_id = $(this).closest("tr").attr("data-id");
    });

    // When confirmed, remove the report and hide the modal
    $("#removeReportModal .btn-primary").off("click").on("click", function() {
        window.ajax_request({
            type: "POST",
            url: "/reports/" + current_id + "/remove",
            on_success: function() {
                $("tr[data-id=\"" + current_id + "\"]").remove();
                $("#removeReportModal").modal("hide");
            }
        });
    });
}

window.manage_init_func("div#reportlist", "index", init_report_list);
