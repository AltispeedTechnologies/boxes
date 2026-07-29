/**
 * @file check_out.js
 * @description Check-out page initialization and submit wiring.
 * @see docs/api/javascript.md
 */

function init_checkout_page() {
    $(document).off("checkoutPackageValid").on("checkoutPackageValid", function(event, pkg) {
        let new_row = $(".visually-hidden")
            .clone()
            .removeClass("visually-hidden")
            .attr("data-row-id", pkg.id);

        let account = `<a href="/accounts/${pkg.account_id}/packages">${pkg.account}</a>`;
        new_row.find("td:nth-child(1)").html(account);

        let tracking_code = `<a href="/packages/${pkg.id}">${pkg.tracking_code}</a>`;
        new_row.find("td:nth-child(2)").html(tracking_code);

        new_row.find("td:nth-child(3)").text("$" + pkg.price);
        new_row.find("td:nth-child(4)").text(pkg.comments);

        $("tbody").append(new_row);
        $("#clearstagedbtn").prop("disabled", false);
    });

    $("#checkOutModal .btn-primary").off("click").on("click", function() {
        let packages_array = Array.from(window.queued_packages);
        let payload = {"ids": packages_array};

        window.ajax_request({
            type: "POST",
            url: "/packages/checkout/submit",
            payload: payload,
            on_success: function(response) {
                window.queued_packages.clear();
                window.location.reload();
            }
        });
    });

    // Clear staged packages without checking them out
    $("#clearstagedbtn").off("click").on("click", function(event) {
        event.preventDefault();
        if (!window.queued_packages || window.queued_packages.size === 0) {
            return;
        }
        if (!window.confirm("Clear staged packages without checking them out?")) {
            return;
        }
        window.queued_packages.clear();
        $("table tbody tr").not(".visually-hidden").remove();
        $(this).prop("disabled", true);
        $(document).trigger("rowsUpdated");
    });
}

$(init_checkout_page);
