function update_ui(current_status) {
    switch (current_status) {
    case 0:
        $(".generating").hide();
        $(".queued").hide();
        $("#generatepdf").prop("disabled", false);
        $("#viewpdf").toggleClass("disabled", true);
        break;
    case 1:
        $(".queued").show();
        $(".generating").hide();
        $("#generatepdf").prop("disabled", true);
        $("#viewpdf").toggleClass("disabled", true);
        break;
    case 2:
        $(".queued").hide();
        $(".generating").show();
        $("#generatepdf").prop("disabled", true);
        $("#viewpdf").toggleClass("disabled", true);
        break;
    case 3:
        $(".generating").hide();
        $(".queued").hide();
        $("#generatepdf").prop("disabled", false);
        $("#viewpdf").toggleClass("disabled", false);
        break;
    case 4:
        $(".generating").hide();
        $(".queued").hide();
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

                // Update the progress bar
                let progress = response.current_progress;
                $("#pdfprogress .progress-bar")
                    .css("width", progress + "%")
                    .attr("aria-valuenow", progress)
                    .text(progress + "%");

                if (response.current_status === 1 || response.current_status === 2) {
                    // Poll every 10 seconds
                    if (!window.report_polling_status) {
                        window.report_polling_status = setInterval(poll_report_status, 10000);
                    }
                } else {
                    clearInterval(window.report_polling_status);
                }
            }
        });
    }
    poll_report_status();

    // When clicking Generate PDF, send the appropriate requests
    $("#generatepdf").off("click").on("click", function() {
        update_ui(1);

        window.ajax_request({
            type: "POST",
            url: "/reports/" + report_id + "/pdf",
            on_success: function() {
                poll_report_status();
            }
        });
    });
}

window.manage_init_func("div#reportviewpage", "view", init_report_view_page);
