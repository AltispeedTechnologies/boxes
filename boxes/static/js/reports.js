function prepare_json_payload() {
    // Specific format enforced on the backend
    let config = {
        fields: [],
    };

    // Report name from user input
    let name = $("#reportname").val();

    // Find all selected fields in order
    $("#newReportModal").find("tbody#field_order").find("tr:not(.visually-hidden)").each(function() {
        config["fields"].push(this.id);
    });

    // Find the selected "sort by field" entry
    config["sort_by"] = $("#newReportModal").find("#sort_by_field").val();

    // Find the "filter by date" selection and store the values appropriately
    let filter_by_date = $("#newReportModal").find("input[name=\"filter_by_date\"]:checked").attr("id");
    config["filter"] = {};

    switch(filter_by_date) {
        case "all_entries":
            config["filter"]["type"] = "all";
            break;
        case "date_range":
            config["filter"]["type"] = filter_by_date;

            let date_range_from = $("#date_range_from").val();
            let date_range_to = $("#date_range_to").val();
            const date_range_from_obj = new Date(date_range_from);
            const date_range_to_obj = new Date(date_range_to);

            if (date_range_from_obj > date_range_to_obj) {
                $("#select_date_range").find(".form-control").addClass("is-invalid");
                $("#select_date_range").find(".invalid-feedback").text("First date must be before (or equal to) the second").show();
                return;
            }

            config["filter"]["start"] = date_range_from;
            config["filter"]["end"] = date_range_to;

            break;
        case "relative_date_range":
            config["filter"]["type"] = filter_by_date;

            let relative_date_range_from = Number($("#relative_date_range_from").val());
            let relative_date_range_to = Number($("#relative_date_range_to").val());
            if (relative_date_range_to <= relative_date_range_from) {
                $("#select_relative_date_range").find(".form-control").addClass("is-invalid");
                $("#select_relative_date_range").find(".invalid-feedback").text("Start value must be greater than end value").show();
                return;
            }

            config["filter"]["start"] = relative_date_range_from;
            config["filter"]["end"] = relative_date_range_to;

            break;
        case "time_period":
            config["filter"]["type"] = filter_by_date;
            let time_period_selected = $("#newReportModal").find("input[name=\"time_period\"]:checked").attr("id");
            config["filter"]["frequency"] = time_period_selected.replace("time_period_", "");
            break;
    }

    // Create the final payload
    let payload = {
        "name": name,
        "config": config,
    };

    return [payload, name];
}

function toggle_disabled_chart_buttons(disabled) {
    $("#weekbtn").attr("disabled", disabled);
    $("#monthbtn").attr("disabled", disabled);
}

function toggle_create_button() {
    // Ensure a field is selected
    let create_disabled = $("#display_fields input[type=\"checkbox\"]:checked").length === 0;

    // Also ensure a name has been entered
    create_disabled = create_disabled || ($("#reportname").val() == "");

    $("#newReportModal .btn-primary").attr("disabled", create_disabled);
}

function toggle_row_arrows() {
    // Enable all buttons
    $(".move-up").prop("disabled", false);
    $(".move-down").prop("disabled", false);

    // Disable the first move up button
    $(".move-up").first().prop("disabled", true);

    // Disable the last move down button
    $(".move-down").last().prop("disabled", true);
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
            toggle_disabled_chart_buttons(false);
        }
    });
}

function init_reports_page() {
    // Initialize the chart
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

    // Chart colors
    window.colors = [
        "rgba(54, 162, 235, 1)",
        "rgba(255, 99, 132, 1)",
        "rgba(245, 179, 66, 1)",
    ];

    // Grab the data and update the chart
    var payload = {filter: "week"};
    update_chart(payload);

    // Toggle button for the chart
    $("#weekbtn").off("click").on("click", function() {
        var payload = {filter: "week"};
        update_chart(payload);

        toggle_disabled_chart_buttons(true);
        $("#weekbtn").addClass("btn-primary").removeClass("btn-light");
        $("#monthbtn").addClass("btn-light").removeClass("btn-primary");
    });

    // Toggle button for the chart
    $("#monthbtn").off("click").on("click", function() {
        var payload = {filter: "month"};
        update_chart(payload);

        toggle_disabled_chart_buttons(true);
        $("#weekbtn").addClass("btn-light").removeClass("btn-primary");
        $("#monthbtn").addClass("btn-primary").removeClass("btn-light");
    });

    // Basic setup for Sort By Field
    $("#sort_by_field").select2({dropdownParent: "#newReportModal", width: "50%"});
    window.select2properheight("#sort_by_field");

    // Handle checkbox changes
    $("#display_fields input[type=\"checkbox\"]").off("change").on("change", function() {
        var select2_dropdown = $("#sort_by_field");
        var option_id = $(this).attr("id");
        var option_text = $("label[for=\"" + option_id + "\"").text();

        if ($(this).is(":checked")) {
            // Add the selected item as a dropdown entry
            var new_option = new Option(option_text, option_id, false, false);
            select2_dropdown.append(new_option).trigger("change");

            // Add the new row for ordering
            let new_row = $("tbody#field_order").find(".visually-hidden")
                .clone()
                .removeClass("visually-hidden")
                .attr("id", option_id);
            new_row.find("td:nth-child(1)").text(option_text);
            new_row.find("button:nth-child(1)").addClass("move-up");
            new_row.find("button:nth-child(2)").addClass("move-down");
            $("tbody#field_order").find(".visually-hidden").before(new_row);
        } else {
            // Remove the option if the checkbox is unchecked
            select2_dropdown.find("option[value=\"" + option_id + "\"]").remove();
            select2_dropdown.trigger("change");

            // Remove the row from ordering
            $("tbody#field_order").find("tr#" + option_id).remove();
        }

        // Only enable the create button if one or more fields are selected
        toggle_create_button();
        toggle_row_arrows();
    });

    // Handle moving a specific row up or down
    $(document).on("click", ".move-up", function() {
        var row = $(this).parents("tr");
        // Do not move the first row
        if (row.index() > 0) {
            row.prev().before(row);
        }

        toggle_row_arrows();
    });
    $(document).on("click", ".move-down", function() {
        var row = $(this).parents("tr");

        // Ensure we are not at the bottom
        if (row.next().length) {
            row.next().after(row);
        }

        toggle_row_arrows();
    });

    // Hook up changes to the report name to enablement of the createbox
    $("#reportname").off("input").on("input", function() {toggle_create_button();});

    // Initialize the date pickers
    $("#select_date_range").find(".form-control").datepicker({
        // Ensure the date picker pops up in the modal
        beforeShow: function(input, inst) {
            $(inst.dpDiv).appendTo("#select_date_range");
        },
        // Manually trigger the input event after date selection
        onSelect: function() {
            $(this).trigger("input");
        }
    });

    // Set up the dynamic filter selection for the add modal
    $("input[name=\"filter_by_date\"]").off("change").on("change", function() {
        // One of: all_entries, date_range, relative_date_range, time_period
        let new_id = $(this).attr("id");

        // Hide all of the potential subselection divs
        $("div.filter_subselection").hide();

        // all_entries does not have additional config options, otherwise show appropriately
        if (new_id !== "all_entries") {
            $("#select_" + new_id).show();
        }
    });

    $("#newReportModal .btn-primary").off("click").on("click", function() {
        const [payload, name] = prepare_json_payload();

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
                new_row.find("td:nth-child(1)").text(name);
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
