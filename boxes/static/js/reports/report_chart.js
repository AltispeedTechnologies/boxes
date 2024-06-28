function toggle_disabled_chart_buttons(disabled) {
    $("#chart_toggle").find("button").attr("disabled", disabled);
}

function update_chart(current_value) {
    $("#loadingicon").show();
    toggle_disabled_chart_buttons(true);

    var payload = {filter: current_value};

    window.ajax_request({
        type: "POST",
        url: "/reports/stats/chart",
        content_type: "application/json",
        payload: JSON.stringify(payload),
        on_success: function(response) {
            // Update the chart data
            let chart_data = response.chart_data;
            window.mainchart.data.labels = chart_data["x_data"];
            window.mainchart.data.datasets = Object.keys(chart_data["y_data"]).map((key, index) => ({
                fill: false,
                label: key,
                backgroundColor: window.colors[index % window.colors.length],
                borderColor: window.colors[index % window.colors.length],
                data: chart_data["y_data"][key]
            }));
            window.mainchart.update();

            // Update the totals
            let total_data = response.total_data;
            $("#emails_sent").text(total_data["emails_sent"]);
            $("#packages_in").text(total_data["packages_in"]);
            $("#packages_out").text(total_data["packages_out"]);

            // Update the Last Updated time
            var last_updated = new Date(response.last_updated).toLocaleString();
            $("#last_updated").text(last_updated);

            // Indicate completion
            $("#loadingicon").hide();
            toggle_disabled_chart_buttons(false);
        }
    });
}

function init_report_chart() {
    // Chart colors
    window.colors = [
        "rgba(54, 162, 235, 1)",
        "rgba(255, 99, 132, 1)",
        "rgba(245, 179, 66, 1)",
    ];

    // Initialize the chart
    window.mainchart = new Chart("mainchart", {
        type: "line",
        data: {
            labels: window.initial_chart_data["x_data"],
            datasets: Object.keys(window.initial_chart_data["y_data"]).map((key, index) => ({
                fill: false,
                label: key,
                backgroundColor: window.colors[index % window.colors.length],
                borderColor: window.colors[index % window.colors.length],
                data: window.initial_chart_data["y_data"][key]
            }))
        },
        options: {
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });

    // Toggle button for the chart
    $("#chart_toggle").find("button").off("click").on("click", function() {
        // Current value for filter
        let current_value = $(this).val();

        // Deselect non-current buttons
        $("#chart_toggle").find("button").filter(function() {
            return $(this).val() !== current_value;
        }).addClass("btn-light").removeClass("btn-primary");

        // Make current button the selected one
        $(this).addClass("btn-primary").removeClass("btn-light");

        // Update the chart to match the current filter
        update_chart(current_value);
    });
}

window.manage_init_func("div#reportdata", "report_chart", init_report_chart);
