function prepare_json_payload() {
    // Specific format enforced on the backend
    let config = {
        fields: [],
    };

    // Report name from user input
    let name = $("#reportname").val();

    // Find all selected fields in order
    $("tbody#field_order").find("tr:not(.visually-hidden)").each(function() {
        config["fields"].push(this.id);
    });

    // Find the selected "sort by field" entry
    config["sort_by"] = $("#sort_by_field").val();

    // Find the "filter by date" selection and store the values appropriately
    let filter_by_date = $("input[name=\"filter_by_date\"]:checked").attr("id");
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
        let time_period_selected = $("input[name=\"time_period\"]:checked").attr("id");
        config["filter"]["frequency"] = time_period_selected.replace("time_period_", "");
        break;
    }

    let filter_by_status = $("input[name=\"filter_by_status\"]:checked").attr("id");
    if (filter_by_status === "all_status") {
        config["state"] = "all";
    } else if (filter_by_status === "checked_in") {
        config["state"] = "in";
    } else if (filter_by_status === "checked_out") {
        config["state"] = "out";
    }

    // Create the final payload
    let payload = {
        "name": name,
        "config": config,
    };

    return payload;
}

function toggle_create_button() {
    // Ensure a field is selected
    let create_disabled = $("#display_fields input[type=\"checkbox\"]:checked").length === 0;

    // Also ensure a name has been entered
    create_disabled = create_disabled || ($("#reportname").val() === "");

    $("#submitconfig").attr("disabled", create_disabled);
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

function init_report_details_page() {
    // Basic setup for Sort By Field
    $("#sort_by_field").select2({width: "50%"});
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

    // Ensure there is a report name and that it is unique
    $("#reportname").off("input").on("input", window.debounce(function() {
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
                        $("#reportname").addClass("is-invalid");
                        $("#reportname").next(".invalid-feedback").text("Duplicate report name").show();

                        // Manually disable the create button
                        $(".btn-primary").attr("disabled", true);
                    }
                }
            });
        }
    }, 500));

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

    // If we are editing an existing report, load the data and appropriately set up the UI
    if ($("#report_config").length === 1) {
        // Set the page header appropriately
        $("#pageheader").text("Edit Report");

        let config = JSON.parse($("#report_config").text());

        // Select the fields in order
        for (const field of config["fields"]) {
            $("#display_fields input[type=\"checkbox\"][id=\"" + field + "\"]").click();
        }

        // Select the proper sort by field
        $("#sort_by_field").val(config["sort_by"]);
        $("#sort_by_field").trigger("change");

        // Select the proper filter by date
        $("input[name=\"filter_by_date\"][id=\"" + config["filter"]["type"] + "\"]").click();

        // Correct subselection values
        switch(config["filter"]["type"]) {
        case "date_range":
            $("#date_range_from").val(config["filter"]["start"]);
            $("#date_range_to").val(config["filter"]["end"]);
            break;
        case "relative_date_range":
            $("#relative_date_range_from").val(config["filter"]["start"]);
            $("#relative_date_range_to").val(config["filter"]["end"]);
            break;
        case "time_period":
            $("input[name=\"time_period\"][id=\"time_period_" + config["filter"]["frequency"] + "\"]").click();
            break;
        }

        switch(config["state"]) {
        case "all":
            $("input[name=\"filter_by_status\"][id=\"all_status\"]").click();
            break;
        case "in":
            $("input[name=\"filter_by_status\"][id=\"checked_in\"]").click();
            break;
        case "out":
            $("input[name=\"filter_by_status\"][id=\"checked_out\"]").click();
            break;
        }
    }

    $("#submitconfig").off("click").on("click", function() {
        const payload = prepare_json_payload();

        let report_id = $(this).attr("data-report-id");
        let submit_url = "/reports/new/submit";
        if (report_id !== "") {
            submit_url = "/reports/" + report_id + "/update";
        }

        window.ajax_request({
            type: "POST",
            url: submit_url,
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function() {
                window.location.href = "/reports/";
            }
        });
    });
}

if ($("div#reportdetailspage").length !== 0) {
    init_report_details_page();
}
