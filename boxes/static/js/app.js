$(document).ready(function() {
    $(".select-select2").select2();

    $(".timestamp").each(function() {
        var iso_timestamp = $(this).data("timestamp");
        var local_time = new Date(iso_timestamp).toLocaleString();
        $(this).text(local_time);
    });
});

function get_cookie(name) {
    var cookie_value = null;
    if (document.cookie && document.cookie !== "") {
        var cookies = document.cookie.split(";");
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookie_value = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookie_value;
}

$("[data-bs-target=\"#print\"]").on("click", function() {
    row_id = $(this).data("row-id");
    window.open("/packages/label?ids=" + row_id);
});
