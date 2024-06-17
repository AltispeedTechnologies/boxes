function prepare_json_payload(modal_name) {
    // Grab the selected modal
    var $modal = $(modal_name);

    // Specific format enforced on the backend
    let config = {
        fields: [],
    };

    // Report name from user input
    let name = $modal.find("#reportname").val();

    // Find all selected fields in order
    $modal.find("tbody#field_order").find("tr:not(.visually-hidden)").each(function() {
        config["fields"].push(this.id);
    });

    // Find the selected "sort by field" entry
    config["sort_by"] = $modal.find("#sort_by_field").val();

    // Find the "filter by date" selection and store the values appropriately
    let filter_by_date = $modal.find("input[name=\"filter_by_date\"]:checked").attr("id");
    config["filter"] = {};

    switch(filter_by_date) {
        case "all_entries":
            config["filter"]["type"] = "all";
            break;
        case "date_range":
            config["filter"]["type"] = filter_by_date;

            let date_range_from = $modal.find("#date_range_from").val();
            let date_range_to = $modal.find("#date_range_to").val();
            const date_range_from_obj = new Date(date_range_from);
            const date_range_to_obj = new Date(date_range_to);

            if (date_range_from_obj > date_range_to_obj) {
                $modal.find("#select_date_range").find(".form-control").addClass("is-invalid");
                $modal.find("#select_date_range").find(".invalid-feedback").text("First date must be before (or equal to) the second").show();
                return;
            }

            config["filter"]["start"] = date_range_from;
            config["filter"]["end"] = date_range_to;

            break;
        case "relative_date_range":
            config["filter"]["type"] = filter_by_date;

            let relative_date_range_from = Number($modal.find("#relative_date_range_from").val());
            let relative_date_range_to = Number($modal.find("#relative_date_range_to").val());
            if (relative_date_range_to <= relative_date_range_from) {
                $modal.find("#select_relative_date_range").find(".form-control").addClass("is-invalid");
                $modal.find("#select_relative_date_range").find(".invalid-feedback").text("Start value must be greater than end value").show();
                return;
            }

            config["filter"]["start"] = relative_date_range_from;
            config["filter"]["end"] = relative_date_range_to;

            break;
        case "time_period":
            config["filter"]["type"] = filter_by_date;
            let time_period_selected = $modal.find("input[name=\"time_period\"]:checked").attr("id");
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

function toggle_create_button(modal_name) {
    // Grab the selected modal
    var $modal = $(modal_name);

    // Ensure a field is selected
    let create_disabled = $modal.find("#display_fields input[type=\"checkbox\"]:checked").length === 0;

    // Also ensure a name has been entered
    create_disabled = create_disabled || ($modal.find("#reportname").val() == "");

    $modal.find(".btn-primary").attr("disabled", create_disabled);
}

function toggle_row_arrows(modal_name) {
    var $modal = $(modal_name);

    // Enable all buttons
    $modal.find(".move-up").prop("disabled", false);
    $modal.find(".move-down").prop("disabled", false);

    // Disable the first move up button
    $modal.find(".move-up").first().prop("disabled", true);

    // Disable the last move down button
    $modal.find(".move-down").last().prop("disabled", true);
}

function clear_modal(modal_name) {
    var $modal = $(modal_name);

    // Clear the report name
    $modal.find("#reportname").val("");

    // Deselect all fields
    $modal.find("#display_fields input[type=\"checkbox\"]:checked").prop("checked", false);

    // Remove all dropdown items
    $modal.find("#sort_by_field").find("option").remove();
    $modal.find("#sort_by_field").trigger("change");

    // Remove all ordering options
    $modal.find("tbody#field_order").find("tr:not(.visually-hidden)").remove();

    // Ensure default of All for dates is set
    $modal.find("input[name=\"filter_by_date\"]:checked").prop("checked", false);    
    $modal.find("input[name=\"filter_by_date\"][id=\"all_entries\"]").prop("checked", true);

    // Hide all subselection divs
    $modal.find("div.filter_subselection").hide();

    // Clear all subselection divs
    $modal.find("div.filter_subselection").find("input").val("");
    $modal.find("div.filter_subselection").find("input:checked").prop("checked", false);
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

function init_chart() {
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
}

function init_modal(modal_name) {
    // Act on a specific modal, so duplicate IDs can be used
    var $modal = $(modal_name);

    // Basic setup for Sort By Field
    $modal.find("#sort_by_field").select2({dropdownParent: modal_name, width: "50%"});
    window.select2properheight("#sort_by_field");

    // Handle checkbox changes
    $modal.find("#display_fields input[type=\"checkbox\"]").off("change").on("change", function() {
        var select2_dropdown = $modal.find("#sort_by_field");
        var option_id = $(this).attr("id");
        var option_text = $modal.find("label[for=\"" + option_id + "\"").text();

        if ($(this).is(":checked")) {
            // Add the selected item as a dropdown entry
            var new_option = new Option(option_text, option_id, false, false);
            select2_dropdown.append(new_option).trigger("change");

            // Add the new row for ordering
            let new_row = $modal.find("tbody#field_order").find(".visually-hidden")
                .clone()
                .removeClass("visually-hidden")
                .attr("id", option_id);
            new_row.find("td:nth-child(1)").text(option_text);
            new_row.find("button:nth-child(1)").addClass("move-up");
            new_row.find("button:nth-child(2)").addClass("move-down");
            $modal.find("tbody#field_order").find(".visually-hidden").before(new_row);
        } else {
            // Remove the option if the checkbox is unchecked
            select2_dropdown.find("option[value=\"" + option_id + "\"]").remove();
            select2_dropdown.trigger("change");

            // Remove the row from ordering
            $("tbody#field_order").find("tr#" + option_id).remove();
        }

        // Only enable the create button if one or more fields are selected
        toggle_create_button(modal_name);
        toggle_row_arrows(modal_name);
    });

    // Handle moving a specific row up or down
    $(document).on("click", ".move-up", function() {
        var row = $(this).parents("tr");
        // Do not move the first row
        if (row.index() > 0) {
            row.prev().before(row);
        }

        toggle_row_arrows(modal_name);
    });
    $(document).on("click", ".move-down", function() {
        var row = $(this).parents("tr");

        // Ensure we are not at the bottom
        if (row.next().length) {
            row.next().after(row);
        }

        toggle_row_arrows(modal_name);
    });

    // Ensure there is a report name and that it is unique
    $modal.find("#reportname").off("input").on("input", window.debounce(function() {
        toggle_create_button();

        let name = $(this).val();
        if (name !== "") {
            let payload = JSON.stringify({"name": name});

            window.ajax_request({
                type: "POST",
                url: "/reports/name",
                payload: payload,
                content_type: "application/json",
                on_success: function(response) {
                    if (!response.unique) {
                        // Show an error on the screen
                        $modal.find("#reportname").addClass("is-invalid");
                        $modal.find("#reportname").next(".invalid-feedback").text("Duplicate report name").show();

                        // Manually disable the create button
                        $modal.find(".btn-primary").attr("disabled", true);
                    }
                }
            });
        }
    }, 500));

    // Initialize the date pickers
    $modal.find("#select_date_range").find(".form-control").datepicker({
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
    $modal.find("input[name=\"filter_by_date\"]").off("change").on("change", function() {
        // One of: all_entries, date_range, relative_date_range, time_period
        let new_id = $(this).attr("id");

        // Hide all of the potential subselection divs
        $modal.find("div.filter_subselection").hide();

        // all_entries does not have additional config options, otherwise show appropriately
        if (new_id !== "all_entries") {
            $modal.find("#select_" + new_id).show();
        }
    });

    // Specific submission actions
    if (modal_name === "#newReportModal") {
        $("#newReportModal .btn-primary").off("click").on("click", function() {
            const [payload, name] = prepare_json_payload(modal_name);

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

                    // Clear the modal
                    clear_modal(modal_name);
                },
                on_response: function() {
                    // Hide the modal
                    $modal.modal("hide");
                }
            });
        });
    }
}

function init_remove_modal() {
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
    init_chart();
    init_modal("#newReportModal");
    init_remove_modal();
}
