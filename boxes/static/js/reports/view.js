function update_ui(current_status) {
    switch (current_status) {
    case 0:
        $(".generating").hide();
        $("#generatepdf").prop("disabled", false);
        $("#viewpdf").toggleClass("disabled", true);
        break;
    case 1:
        $(".generating").show();
        $("#generatepdf").prop("disabled", true);
        $("#viewpdf").toggleClass("disabled", true);
        break;
    case 2:
        $(".generating").hide();
        $("#generatepdf").prop("disabled", false);
        $("#viewpdf").toggleClass("disabled", false);
        break;
    case 3:
        $(".generating").hide();
        $("#generatepdf").prop("disabled", false);
        $("#viewpdf").toggleClass("disabled", true);
        break;
    }
}

function init_report_view_page() {
    // Get the report ID
    let report_id = $("#reportviewpage").data("report-id");

    // Update the UI based on the current state of the report result
    function poll_report_status() {
        window.ajax_request({
            type: "GET",
            url: "/reports/" + report_id + "/pdf",
            on_success: function(response) {
                // Update the UI, if anything changes
                update_ui(response.current_status);

                if (response.current_status !== 1) {
                    clearInterval(window.report_polling_status);
                }
            }
        });
    }
    // Poll every 30 seconds
    poll_report_status();
    clearInterval(window.report_polling_status);
    window.report_polling_status = setInterval(poll_report_status, 30000);

    // When clicking Generate PDF, send the appropriate requests
    $("#generatepdf").off("click").on("click", function() {
        update_ui(1);

        window.ajax_request({
            type: "POST",
            url: "/reports/" + report_id + "/pdf",
            on_success: function() {
                // Poll every 30 seconds
                clearInterval(window.report_polling_status);
                window.report_polling_status = setInterval(poll_report_status, 30000);
            }
        });
    });
}

if ($("div#reportviewpage").length !== 0) {
    init_report_view_page();
}
