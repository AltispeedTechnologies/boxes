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
        }
    });

    window.colors = [
        "rgba(54, 162, 235, 1)",
        "rgba(255, 99, 132, 1)",
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
}

if ($("div#reportspage").length !== 0) {
    init_reports_page();
}
