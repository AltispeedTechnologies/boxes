$(document).ready(function() {
    $('[data-bs-target="#editModal"]').on("click", function () {
        var row_id = $(this).data("row-id");
        var tr = $(this).closest("tr");
        var package_data = {};

        // Only grab packages with a defined data type
        tr.find("td[data-type]").each(function() {
            var text = $(this).text().trim();
            var type = $(this).data("type");
            if (text !== "") {
                package_data[type] = text;
                console.log(type + " - " + text);
            }
        });

        $("#tracking_code").val(package_data.tracking_code);
        $("#price").val(package_data.price.replace("$", ""));
        $("#comments").val(package_data.comments);
    });
});
