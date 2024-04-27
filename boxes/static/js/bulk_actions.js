$(document).ready(function() {
    let csrf_token = window.get_cookie("csrftoken");

    $("[data-bs-target=\"#bulkPrint\"]").on("click", function() {
        var row_ids = Array.from(window.selected_packages).join(",");
        window.open("/packages/label?ids=" + row_ids);
    });
});

$(document).on("selectedPackagesUpdated", function(event) {
    $("#bulkprintbtn").prop("disabled", (window.selected_packages.size == 0));
});
