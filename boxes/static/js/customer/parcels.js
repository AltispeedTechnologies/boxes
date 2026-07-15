/**
 * @file customer/parcels.js
 * @description Reserve selected parcels for an open pickup day.
 */

function init_customer_parcels_page() {
    function update_reserve_enabled() {
        const has_day = !!$("#pickupdayselect").val();
        const has_pkgs = window.selected_packages && window.selected_packages.size > 0;
        $("#reservepickupbtn").prop("disabled", !(has_day && has_pkgs));
    }

    $("#pickupdayselect").off("change").on("change", update_reserve_enabled);
    $(document).on("selectedPackagesUpdated", update_reserve_enabled);
    update_reserve_enabled();

    $("#reservepickupbtn").off("click").on("click", function() {
        const date = $("#pickupdayselect").val();
        const package_ids = Array.from(window.selected_packages || []).map(function(x) {
            return parseInt(x, 10);
        }).filter(function(x) { return !isNaN(x); });

        if (!date || !package_ids.length) {
            return;
        }

        $("#reservestatus").html("<i class=\"fas fa-spinner fa-spin\"></i> Saving…");
        $("#reservepickupbtn").prop("disabled", true);

        window.ajax_request({
            type: "POST",
            url: "/customer/parcels/reserve",
            payload: JSON.stringify({package_ids: package_ids, date: date}),
            content_type: "application/json",
            on_success: function(response) {
                $("#reservestatus").html(
                    "<span class=\"text-success\">Reserved " +
                    ((response.created || 0) + (response.updated || 0)) +
                    " package(s) for " + response.date + "</span>"
                );
                window.location.reload();
            },
            on_response: function(response) {
                if (!response.success) {
                    update_reserve_enabled();
                    $("#reservestatus").html("<span class=\"text-danger\">Reservation failed</span>");
                }
            }
        });
    });
}

$(init_customer_parcels_page);
