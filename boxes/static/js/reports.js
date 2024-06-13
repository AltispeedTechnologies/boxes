function toggle_disabled_buttons(disabled) {
    $("#weekbtn").attr("disabled", disabled);
    $("#monthbtn").attr("disabled", disabled);
}

function update_chart(payload) {
    $("#loadingicon").show();

    window.ajax_request({
        type: "POST",
        url: "/reports/stats/chart",
        content_type: "application/json",
        payload: JSON.stringify(payload),
        on_success: function(response) {
            window.mainchart.data.labels = response.x_data;
            window.mainchart.data.datasets = Object.keys(response.y_data).map((key, index) => ({
                fill: false,
                label: key,
                backgroundColor: window.colors[index % window.colors.length],
                borderColor: window.colors[index % window.colors.length],
                data: response.y_data[key]
            }));

            window.mainchart.update();

            $("#loadingicon").hide();
            toggle_disabled_buttons(false);
        }
    });
}

function init_reports_page() {
    window.mainchart = new Chart("mainchart", {
        type: "line",
        data: {
            labels: [],
            datasets: []
        },
        options: {
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });

    window.colors = [
        "rgba(54, 162, 235, 1)",
        "rgba(255, 99, 132, 1)",
        "rgba(245, 179, 66, 1)",
    ];

    var payload = {filter: "week"};
    update_chart(payload);

    $("#weekbtn").off("click").on("click", function() {
        var payload = {filter: "week"};
        update_chart(payload);

        toggle_disabled_buttons(true);
        $("#weekbtn").addClass("btn-primary").removeClass("btn-light");
        $("#monthbtn").addClass("btn-light").removeClass("btn-primary");
    });

    $("#monthbtn").off("click").on("click", function() {
        var payload = {filter: "month"};
        update_chart(payload);

        toggle_disabled_buttons(true);
        $("#weekbtn").addClass("btn-light").removeClass("btn-primary");
        $("#monthbtn").addClass("btn-primary").removeClass("btn-light");
    });

    $("#sort_by_field").select2({dropdownParent: "#newReportModal"});
    window.select2properheight("#sort_by_field");
    // Handle checkbox changes
    $("#display_fields input[type=\"checkbox\"]").change(function() {
        var select2_dropdown = $("#sort_by_field");
        var option_id = $(this).attr("id");
        var option_text = $("label[for=\"" + option_id + "\"").text();

        if ($(this).is(":checked")) {
            // Add the selected item as a dropdown entry
            var new_option = new Option(option_text, option_id, false, false);
            select2_dropdown.append(new_option).trigger("change");
        } else {
            // Remove the option if the checkbox is unchecked
            select2_dropdown.find("option[value=\"" + option_id + "\"]").remove();
            select2_dropdown.trigger("change");
        }
    });

    $("#newReportModal .btn-primary").off("click").on("click", function() {
        // Specific format enforced on the backend
        let config = {
            fields: [],
        };

        // Report name from user input
        let name = $("#reportname").val();

        // Find all selected fields
        $("#newReportModal").find("#display_fields input:checked").each(function() {
            config["fields"].push(this.id);
        });

        // Find the selected "sort by field" entry
        config["sort_by"] = $("#newReportModal").find("#sort_by_field").val();

        // Create the final payload
        let payload = {
            "name": name,
            "config": config,
        };

        window.ajax_request({
            type: "POST",
            url: "/reports/new",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function(response) {
                // If the table is not present, a reload is easier
                if ($("tbody#reports").length === 0) {
                    window.location.reload();
                }
 
                // Add it visually
                let new_row = $("tbody#reports").find(".visually-hidden")
                    .clone()
                    .removeClass("visually-hidden")
                    .attr("data-id", response.id);
                new_row.find("td:nth-child(1)").text(report_name);
                $("tbody#reports").find(".visually-hidden").before(new_row);
            },
            on_response: function() {
                // Hide the modal
                $("#newReportModal").modal("hide");
            }
        });
    });

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
            on_success: function(response) {
                $("tr[data-id=\"" + current_id + "\"]").remove();
                $("#removeReportModal").modal("hide");
            }
        });
    });
}

if ($("div#reportspage").length !== 0) {
    init_reports_page();
}
