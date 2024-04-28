$(document).ready(function() {
    let csrf_token = window.get_cookie("csrftoken");

    $("[data-bs-target=\"#bulkPrint\"]").on("click", function() {
        var row_ids = Array.from(window.selected_packages).join(",");
        window.open("/packages/label?ids=" + row_ids);
    });
});

$(document).on("selectedPackagesUpdated", function(event) {
    var no_selected_packages = (window.selected_packages.size == 0);

    $("#bulkprintbtn").prop("disabled", no_selected_packages);
    $("#bulkeditbtn").prop("disabled", no_selected_packages);
});
