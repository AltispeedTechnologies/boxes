/**
 * @file reports/report_chart.js
 * @description Chart.js rendering for dashboard stats.
 * @see docs/api/javascript.md
 */


/**
 * Build Chart.js datasets from packages_by_carrier y_data.
 */
function carrier_datasets(y_data) {
    return Object.keys(y_data || {}).map((key, index) => ({
        fill: false,
        label: key,
        backgroundColor: window.colors[index % window.colors.length],
        borderColor: window.colors[index % window.colors.length],
        data: y_data[key]
    }));
}

/**
 * Update or create the packages-by-carrier chart.
 */
function update_carrier_chart(packages_by_carrier) {
    if (!window.carrierchart || !packages_by_carrier) {
        return;
    }
    window.carrierchart.data.labels = packages_by_carrier["x_data"] || [];
    window.carrierchart.data.datasets = carrier_datasets(packages_by_carrier["y_data"]);
    window.carrierchart.update();
}

function toggle_disabled_chart_buttons(disabled) {
    $("#chart_toggle").find("button").attr("disabled", disabled);
}

/**
 * Fetch and redraw the dashboard chart for a frequency.
 */
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

            // Packages by carrier / day series from report_stats_chart
            update_carrier_chart(chart_data["packages_by_carrier"]);

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

/**
 * Create the initial Chart.js instance.
 */
function init_report_chart() {
    // Chart colors
    window.colors = [
        "rgba(54, 162, 235, 1)",
        "rgba(255, 99, 132, 1)",
        "rgba(245, 179, 66, 1)",
        "rgba(75, 192, 192, 1)",
        "rgba(153, 102, 255, 1)",
        "rgba(255, 159, 64, 1)",
        "rgba(201, 203, 207, 1)",
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

    // Packages-by-carrier-by-day chart (check-ins grouped by carrier name + day)
    let initial_carrier = window.initial_chart_data["packages_by_carrier"] || {x_data: [], y_data: {}};
    window.carrierchart = new Chart("carrierchart", {
        type: "line",
        data: {
            labels: initial_carrier["x_data"] || [],
            datasets: carrier_datasets(initial_carrier["y_data"])
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

        // Update the current browser URL with the new frequency
        var url = new URL(window.location.href);
        var params = new URLSearchParams(url.search);

        // Actually set the URL and push to history
        params.set("frequency", current_value);
        url.search = params.toString();
        window.history.pushState({ path: url.href }, "", url.href);
    });
}

$(init_report_chart);
