function toggle_disabled_chart_buttons(disabled) {
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
            labels: window.initial_x_data,
            datasets: Object.keys(window.initial_y_data).map((key, index) => ({
                fill: false,
                label: key,
                backgroundColor: window.colors[index % window.colors.length],
                borderColor: window.colors[index % window.colors.length],
                data: window.initial_y_data[key]
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

window.manage_init_func("div#reportdata", "chart", init_report_chart);
